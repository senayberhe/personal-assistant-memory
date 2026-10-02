"""Interactive text chat in the terminal, built with rich."""

import logging
from collections.abc import Callable

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from assistant.errors import AgentError, PermissionDeniedError, ToolError
from assistant.interfaces.commands import ChatCommands
from assistant.interfaces.prompter import RichPrompter
from assistant.observability import request_context

logger = logging.getLogger(__name__)

WELCOME = (
    "Chat with your assistant. It can open apps and websites, "
    "search, and remember facts about you.\n"
    "Type [bold cyan]/help[/] for commands, [bold cyan]/quit[/] to exit."
)


class TextChat:
    """
    Read a message, show the reply, repeat.

    Messages starting with "/" are commands (see ChatCommands);
    everything else goes to the agent.
    """

    def __init__(
        self,
        agent,
        commands: ChatCommands,
        prompter: RichPrompter,
        console: Console | None = None,
        read_input: Callable[[], str] | None = None,
    ):
        """
        read_input:
            Returns the next line typed by the user. Injected in
            tests; defaults to a styled console prompt.
        """

        self.agent = agent
        self.commands = commands
        self.prompter = prompter
        self.console = console or prompter.console
        self.read_input = read_input or self._prompt

        # Show tool activity as it happens.
        self.agent.on_tool_call = self._show_tool_call

    def run(self) -> None:
        self.console.print(
            Panel(WELCOME, title="Assistant", border_style="cyan")
        )

        while True:
            try:
                text = self.read_input().strip()

            except (EOFError, KeyboardInterrupt):
                self.console.print()
                break

            if not text:
                continue

            if self.commands.is_command(text):
                result = self.commands.handle(text)

                if result.output is not None:
                    self.console.print(result.output)

                if result.quit:
                    break

                continue

            self._answer(text)

        self.console.print("[dim]Goodbye.[/]")

    def _prompt(self) -> str:
        return self.console.input("\n[bold green]You ›[/] ")

    def _answer(self, text: str) -> None:
        with request_context():
            try:
                with self.console.status(
                    "[cyan]Thinking…", spinner="dots"
                ) as status:
                    self.prompter.active_status = status

                    reply = self.agent.run(text)

            except PermissionDeniedError:
                self._notice("Okay, I won't do that.")
                return

            except ToolError:
                logger.exception("Tool execution failed.")
                self._notice("I couldn't complete that action.", error=True)
                return

            except AgentError:
                logger.exception("Agent failed.")
                self._notice(
                    "I couldn't reach the language model. Check your "
                    "internet connection and OPENAI_API_KEY.",
                    error=True,
                )
                return

            except Exception:
                logger.exception("Unexpected assistant error.")
                self._notice(
                    "Something unexpected went wrong (see logs/assistant.log).",
                    error=True,
                )
                return

            finally:
                self.prompter.active_status = None

        self.console.print(
            Panel(
                Markdown(reply),
                title="Assistant",
                title_align="left",
                border_style="cyan",
            )
        )

    def _show_tool_call(
        self,
        name: str,
        arguments: dict,
    ) -> None:

        details = ", ".join(f"{key}={value!r}" for key, value in arguments.items())

        self.console.print(
            Text(f"  ⚙ {name}({details})", style="dim")
        )

    def _notice(
        self,
        message: str,
        error: bool = False,
    ) -> None:

        self.console.print(
            Text(message, style="red" if error else "yellow")
        )
