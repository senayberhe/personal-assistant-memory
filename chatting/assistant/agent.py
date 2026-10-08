"""
The agent: one user message in, one reply out.

For each message it saves anything worth remembering, recalls
related memories, then runs the model's tool-calling loop until
the model answers with text.
"""

import json
import logging
from collections.abc import Callable
from typing import cast

from openai import OpenAI, OpenAIError
from openai.types.responses import ToolParam

from assistant.errors import AgentError, PermissionDeniedError, ToolError
from assistant.memory import ConversationMemory
from assistant.memory.context import format_memory_context
from assistant.memory.guard import SensitiveMemoryError
from assistant.memory.manager import MemoryApprovalDeclined
from assistant.observability import measure_time
from assistant.safety import SensitiveDataDetector, clean_text
from config.settings import Settings

logger = logging.getLogger(__name__)

MAX_INPUT_CHARACTERS = 2_000

_BASE_INSTRUCTIONS = (
    "You are a helpful personal assistant running on macOS. "
    "Use the available tools when the user asks you to open an "
    "application, open a website, or search. If a tool fails, "
    "briefly tell the user what went wrong. Never reveal or repeat "
    "secrets such as passwords or API keys."
)

VOICE_INSTRUCTIONS = (
    f"{_BASE_INSTRUCTIONS} Your replies are spoken aloud, so keep "
    "them short, conversational, and free of markdown or lists."
)

TEXT_INSTRUCTIONS = (
    f"{_BASE_INSTRUCTIONS} Your replies are shown in a terminal "
    "chat. Keep them concise; simple Markdown is allowed."
)

# Backwards-compatible name.
INSTRUCTIONS = VOICE_INSTRUCTIONS

ToolCallListener = Callable[[str, dict], None]


class VoiceAgent:
    """
    Runs the LLM tool-calling loop for a single user request.

    Used by both the voice and the text interface; only the
    `instructions` differ.
    """

    def __init__(
        self,
        executor,
        tool_definitions: list[dict],
        settings: Settings,
        memory_manager=None,
        memory_extractor=None,
        client=None,
        conversation: ConversationMemory | None = None,
        instructions: str = VOICE_INSTRUCTIONS,
        on_tool_call: ToolCallListener | None = None,
        require_memory_approval: bool = False,
        detector: SensitiveDataDetector | None = None,
    ):
        """
        on_tool_call:
            Optional callback(tool_name, arguments), called before
            each tool runs. The text UI uses it to show activity.
        require_memory_approval:
            Ask the user before saving automatically detected facts.
        """

        self.executor = executor
        self.tool_definitions = tool_definitions
        self.settings = settings
        self.memory_manager = memory_manager
        self.memory_extractor = memory_extractor
        self.instructions = instructions
        self.on_tool_call = on_tool_call
        self.require_memory_approval = require_memory_approval
        self.detector = detector or SensitiveDataDetector()

        self.client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.api_timeout,
        )

        self.conversation = conversation or ConversationMemory()

    def run(
        self,
        text: str,
    ) -> str:

        text = clean_text(text, MAX_INPUT_CHARACTERS + 1)

        if not text:
            return "I didn't catch that."

        if len(text) > MAX_INPUT_CHARACTERS:
            return (
                "That message is too long. Please keep it under "
                f"{MAX_INPUT_CHARACTERS} characters."
            )

        notices = self._remember(text)

        # Detected secrets never leave this machine: the model and
        # the conversation history only ever see [REDACTED].
        safe_text = self.detector.redact(text)

        if safe_text != text:
            notices.append(
                "Note: sensitive information in the user's message was "
                "replaced with [REDACTED] before it reached you. Do not "
                "ask the user to repeat it."
            )

        input_items: list = [
            {
                "role": "developer",
                "content": self._build_instructions(safe_text, notices),
            },
            *self.conversation.get_messages(),
            {
                "role": "user",
                "content": safe_text,
            },
        ]

        for step in range(self.settings.max_agent_steps):

            response = self._create_response(input_items)

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                reply = response.output_text.strip() or "Done."

                self.conversation.add_user_message(safe_text)
                self.conversation.add_assistant_message(reply)

                return reply

            input_items.extend(response.output)

            for call in function_calls:
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": self._execute_tool(call),
                    }
                )

            logger.debug(
                "Agent step %d executed %d tool call(s).",
                step + 1,
                len(function_calls),
            )

        raise AgentError(
            f"Agent exceeded {self.settings.max_agent_steps} steps."
        )

    def reset_conversation(self) -> None:
        """Forget the short-term conversation (not long-term memory)."""

        self.conversation.clear()

    # --------------------------------------------------
    # Model
    # --------------------------------------------------

    def _create_response(
        self,
        input_items: list,
    ):

        try:
            with measure_time("llm_response"):
                return self.client.responses.create(
                    model=self.settings.model,
                    input=input_items,
                    # The definitions are plain dicts in the
                    # shape the API expects (tools/builtin.py).
                    tools=cast(list[ToolParam], self.tool_definitions),
                )

        except OpenAIError as error:
            raise AgentError(
                "The language model request failed."
            ) from error

    # --------------------------------------------------
    # Tools
    # --------------------------------------------------

    def _execute_tool(
        self,
        call,
    ) -> str:

        try:
            arguments = json.loads(call.arguments or "{}")

        except json.JSONDecodeError:
            return f"Error: invalid JSON arguments for '{call.name}'."

        if self.on_tool_call is not None:
            try:
                self.on_tool_call(call.name, arguments)

            except Exception:
                logger.exception("on_tool_call listener failed.")

        try:
            with measure_time(f"tool:{call.name}"):
                return self.executor.execute(call.name, arguments)

        except PermissionDeniedError:
            # The user said no; stop the whole request.
            raise

        except ToolError as error:
            # Let the model see the failure so it can
            # retry or explain it to the user.
            return f"Error: {error}"

    # --------------------------------------------------
    # Memory
    # --------------------------------------------------

    def _build_instructions(
        self,
        text: str,
        notices: list[str],
    ) -> str:

        sections = [self.instructions, *notices]

        if self.memory_manager is not None:
            try:
                memories = [
                    ranked.memory
                    for ranked in self.memory_manager.recall_ranked(
                        text,
                        top_k=5,
                    )
                ]

                sections.append(format_memory_context(memories))

            except Exception:
                logger.exception("Memory recall failed.")

        return "\n\n".join(sections)

    def _remember(
        self,
        text: str,
    ) -> list[str]:
        """
        Save facts from the message.

        Returns notices for the model, e.g. that sensitive data
        was deliberately not saved.
        """

        if self.memory_manager is None or self.memory_extractor is None:
            return []

        notices = []

        for item in self.memory_extractor.extract(text):
            try:
                # upsert runs the full pipeline: duplicates are
                # ignored and conflicts go through the policy.
                self.memory_manager.upsert(
                    content=item["content"],
                    memory_type=item["memory_type"],
                    source="conversation",
                    require_approval=self.require_memory_approval,
                )

            except MemoryApprovalDeclined:
                notices.append(
                    "Note: the user chose not to save this to long-term "
                    "memory. Do not say that you will remember it."
                )

            except SensitiveMemoryError as error:
                logger.warning(
                    "Refused to store sensitive memory: %s",
                    ", ".join(error.kinds),
                )

                notices.append(
                    "Note: the user's last message contained sensitive "
                    f"information ({', '.join(error.kinds)}). It was NOT "
                    "saved to long-term memory. If they asked you to "
                    "remember it, tell them you do not store secrets."
                )

            except Exception:
                logger.exception("Saving memory failed.")

        return notices
