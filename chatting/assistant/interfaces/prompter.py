"""Yes/no questions in the rich terminal UI."""

from rich.console import Console
from rich.prompt import Confirm
from rich.status import Status


class RichPrompter:
    """
    Asks the user to confirm risky actions.

    The same prompter backs tool permissions and memory
    confirmations. While the agent is working a "Thinking…"
    spinner is shown; it is paused during a question so the
    prompt is not overwritten.
    """

    def __init__(
        self,
        console: Console,
    ):
        self.console = console
        self.active_status: Status | None = None

    def confirm(
        self,
        question: str,
    ) -> bool:

        status = self.active_status

        if status is not None:
            status.stop()

        try:
            self.console.print()
            self.console.print(f"[bold yellow]⚠ {question}[/]")

            return Confirm.ask(
                "Allow?",
                console=self.console,
                default=False,
            )

        except (EOFError, KeyboardInterrupt):
            # No answer means no.
            return False

        finally:
            if status is not None:
                status.start()
