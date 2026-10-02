import json
import logging

from openai import OpenAI, OpenAIError

from assistant.errors import (
    AgentError,
    PermissionDeniedError,
    ToolError,
)
from assistant.memory import ConversationMemory
from assistant.memory_context import format_memory_context
from assistant.memory_deduplicator import MemoryDeduplicator
from assistant.observability import measure_time
from config.settings import Settings


logger = logging.getLogger(__name__)


INSTRUCTIONS = (
    "You are a helpful voice assistant running on macOS. "
    "Your replies are spoken aloud, so keep them short, "
    "conversational, and free of markdown or lists. "
    "Use the available tools when the user asks you to "
    "open an application, open a website, or search. "
    "If a tool fails, briefly tell the user what went wrong."
)


class VoiceAgent:
    """
    Runs the LLM tool-calling loop for a single user request.

    The agent recalls relevant long-term memories, sends the
    conversation to the model, executes any tool calls through
    the ToolExecutor, and returns the final spoken reply.
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
    ):
        self.executor = executor
        self.tool_definitions = tool_definitions
        self.settings = settings
        self.memory_manager = memory_manager
        self.memory_extractor = memory_extractor

        self.client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.api_timeout,
        )

        self.conversation = (
            conversation or ConversationMemory()
        )

        self.deduplicator = (
            MemoryDeduplicator(memory_manager)
            if memory_manager is not None
            else None
        )

    def run(
        self,
        text: str,
    ) -> str:

        text = text.strip()

        if not text:
            return "I didn't catch that."

        self._remember(text)

        input_items: list = [
            {
                "role": "developer",
                "content": self._build_instructions(text),
            },
            *self.conversation.get_messages(),
            {
                "role": "user",
                "content": text,
            },
        ]

        for step in range(
            self.settings.max_agent_steps
        ):

            response = self._create_response(
                input_items
            )

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:

                reply = (
                    response.output_text.strip()
                    or "Done."
                )

                self.conversation.add_user_message(text)
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
            f"Agent exceeded "
            f"{self.settings.max_agent_steps} steps."
        )

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
                    tools=self.tool_definitions,
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
            arguments = json.loads(
                call.arguments or "{}"
            )

        except json.JSONDecodeError:
            return (
                f"Error: invalid JSON arguments "
                f"for '{call.name}'."
            )

        try:

            with measure_time(f"tool:{call.name}"):

                return self.executor.execute(
                    call.name,
                    arguments,
                )

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
    ) -> str:

        if self.memory_manager is None:
            return INSTRUCTIONS

        try:
            memories = [
                ranked.memory
                for ranked in self.memory_manager.recall_ranked(
                    text,
                    top_k=5,
                )
            ]

        except Exception:
            logger.exception(
                "Memory recall failed."
            )
            return INSTRUCTIONS

        return (
            f"{INSTRUCTIONS}\n\n"
            f"{format_memory_context(memories)}"
        )

    def _remember(
        self,
        text: str,
    ) -> None:

        if (
            self.memory_manager is None
            or self.memory_extractor is None
            or self.deduplicator is None
        ):
            return

        try:

            for item in self.memory_extractor.extract(text):

                if self.deduplicator.find_duplicate(
                    item["content"]
                ):
                    continue

                self.memory_manager.remember(
                    content=item["content"],
                    memory_type=item["memory_type"],
                    source="conversation",
                )

        except Exception:
            logger.exception(
                "Saving memory failed."
            )
