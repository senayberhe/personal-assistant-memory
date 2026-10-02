"""
Slash commands for the text chat (/memories, /forget, ...).

Commands return rich renderables instead of printing, so they can
be tested without a terminal and reused by other interfaces.
"""

from collections.abc import Callable
from dataclasses import dataclass

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from assistant.memory import Memory, MemoryManager
from assistant.memory.events.metrics import MemoryMetrics
from assistant.tools.metrics import Metrics as ToolMetrics

SHORT_ID_LENGTH = 8


class CommandError(Exception):
    """A user mistake in a command (shown in red, no traceback)."""


@dataclass(frozen=True)
class CommandResult:
    output: RenderableType | None = None
    quit: bool = False


@dataclass(frozen=True)
class _Command:
    handler: Callable[[str], CommandResult]
    usage: str
    description: str


class ChatCommands:
    """Parses and runs slash commands."""

    def __init__(
        self,
        memory_manager: MemoryManager | None,
        reset_conversation: Callable[[], None],
        confirm: Callable[[str], bool],
        memory_metrics: MemoryMetrics | None = None,
        tool_metrics: ToolMetrics | None = None,
    ):
        self.memory_manager = memory_manager
        self.reset_conversation = reset_conversation
        self.confirm = confirm
        self.memory_metrics = memory_metrics
        self.tool_metrics = tool_metrics

        self._commands: dict[str, _Command] = {
            "help": _Command(self._help, "/help", "Show this help."),
            "memories": _Command(
                self._memories,
                "/memories [search]",
                "List saved memories, or search them.",
            ),
            "remember": _Command(
                self._remember, "/remember <fact>", "Save a fact."
            ),
            "forget": _Command(
                self._forget, "/forget <id>", "Delete a memory."
            ),
            "history": _Command(
                self._history, "/history <id>", "Show earlier versions."
            ),
            "restore": _Command(
                self._restore,
                "/restore <id> <version>",
                "Bring back an earlier version.",
            ),
            "stats": _Command(
                self._stats, "/stats", "Memory and tool statistics."
            ),
            "clear": _Command(
                self._clear,
                "/clear",
                "Start a new conversation (memories are kept).",
            ),
            "quit": _Command(self._quit, "/quit", "Exit."),
        }

        self._aliases = {"exit": "quit", "q": "quit", "?": "help"}

    @staticmethod
    def is_command(text: str) -> bool:
        return text.startswith("/")

    def handle(
        self,
        text: str,
    ) -> CommandResult:

        name, _, argument = text[1:].strip().partition(" ")
        name = self._aliases.get(name.lower(), name.lower())

        command = self._commands.get(name)

        if command is None:
            return _error(f"Unknown command '/{name}'. Type /help.")

        try:
            return command.handler(argument.strip())

        except CommandError as error:
            return _error(str(error))

        except ValueError as error:
            # Validation errors from the memory system, e.g. a
            # rejected secret. Safe to show: they never echo it.
            return _error(str(error))

    # --------------------------------------------------
    # Commands
    # --------------------------------------------------

    def _help(self, _: str) -> CommandResult:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column()

        for command in self._commands.values():
            table.add_row(command.usage, command.description)

        return CommandResult(table)

    def _memories(self, query: str) -> CommandResult:
        manager = self._require_memory()

        if query:
            ranked = manager.recall_ranked(query, top_k=10)

            if not ranked:
                return _info("No matching memories.")

            table = _memory_table(f"Memories matching “{query}”", score=True)

            for item in ranked:
                _add_memory_row(table, item.memory, f"{item.final_score:.2f}")

            return CommandResult(table)

        memories = manager.get_all()

        if not memories:
            return _info(
                "No memories yet. Try “/remember I prefer Python”."
            )

        table = _memory_table(f"Saved memories ({len(memories)})")

        for memory in memories:
            _add_memory_row(table, memory)

        return CommandResult(table)

    def _remember(self, fact: str) -> CommandResult:
        manager = self._require_memory()

        if not fact:
            raise CommandError("Usage: /remember <fact>")

        known = {memory.id: memory.version for memory in manager.get_all()}

        memory = manager.upsert(fact, source="user")

        if memory.id not in known:
            return _success(f"Saved as {_short(memory.id)}.")

        if memory.version != known[memory.id]:
            return _success(
                f"Updated {_short(memory.id)} (now version {memory.version})."
            )

        return _info(f"Already remembered as {_short(memory.id)}.")

    def _forget(self, argument: str) -> CommandResult:
        memory = self._find(argument, "/forget <id>")

        if not self.confirm(f'Delete memory "{memory.content}"?'):
            return _info("Kept.")

        self._require_memory().forget(memory.id)

        return _success(f"Forgot {_short(memory.id)}.")

    def _history(self, argument: str) -> CommandResult:
        memory = self._find(argument, "/history <id>")
        history = self._require_memory().get_history(memory.id)

        table = Table(title=f"History of {_short(memory.id)}")
        table.add_column("Version", justify="right", style="cyan")
        table.add_column("Content")
        table.add_column("Replaced", style="dim")

        for version in history:
            table.add_row(
                str(version.version),
                version.content,
                version.recorded_at.strftime("%Y-%m-%d %H:%M"),
            )

        table.add_row(
            f"[bold]{memory.version}[/]",
            f"[bold]{memory.content}[/]",
            "current",
        )

        return CommandResult(table)

    def _restore(self, argument: str) -> CommandResult:
        usage = "/restore <id> <version>"
        memory_id, _, version_text = argument.partition(" ")

        if not version_text.strip().isdigit():
            raise CommandError(f"Usage: {usage}")

        memory = self._find(memory_id, usage)

        restored = self._require_memory().restore_memory_version(
            memory.id,
            int(version_text),
        )

        return _success(
            f"Restored version {version_text.strip()} as "
            f"version {restored.version}: {restored.content}"
        )

    def _stats(self, _: str) -> CommandResult:
        table = Table(title="Statistics")
        table.add_column("Metric")
        table.add_column("Value", justify="right", style="cyan")

        if self.memory_metrics is not None:
            for name, value in self.memory_metrics.snapshot().items():
                table.add_row(f"Memories {name}", str(value))

        if self.tool_metrics is not None:
            for name, tool in sorted(self.tool_metrics.tools.items()):
                table.add_row(
                    f"Tool {name}",
                    f"{tool.successes}/{tool.calls} ok, "
                    f"{tool.average_latency:.2f}s avg",
                )

        if table.row_count == 0:
            return _info("No activity yet.")

        return CommandResult(table)

    def _clear(self, _: str) -> CommandResult:
        self.reset_conversation()

        return _info("Started a new conversation. Saved memories are kept.")

    def _quit(self, _: str) -> CommandResult:
        return CommandResult(quit=True)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _require_memory(self) -> MemoryManager:
        if self.memory_manager is None:
            raise CommandError("Memory is not enabled.")

        return self.memory_manager

    def _find(
        self,
        id_prefix: str,
        usage: str,
    ) -> Memory:
        """Find a memory by (a unique prefix of) its ID."""

        id_prefix = id_prefix.strip()

        if not id_prefix:
            raise CommandError(f"Usage: {usage}")

        matches = [
            memory
            for memory in self._require_memory().get_all()
            if memory.id.startswith(id_prefix)
        ]

        if not matches:
            raise CommandError(f"No memory with ID '{id_prefix}'.")

        if len(matches) > 1:
            raise CommandError(
                f"'{id_prefix}' matches {len(matches)} memories; "
                "type more of the ID."
            )

        return matches[0]


def _short(memory_id: str) -> str:
    return memory_id[:SHORT_ID_LENGTH]


def _memory_table(title: str, score: bool = False) -> Table:
    table = Table(title=title)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Memory")
    table.add_column("v", justify="right", style="dim")

    if score:
        table.add_column("Score", justify="right", style="green")
    else:
        table.add_column("Saved", style="dim", no_wrap=True)

    return table


def _add_memory_row(
    table: Table,
    memory: Memory,
    score: str | None = None,
) -> None:

    table.add_row(
        _short(memory.id),
        memory.memory_type,
        memory.content,
        str(memory.version),
        score or memory.created_at.strftime("%Y-%m-%d"),
    )


def _success(message: str) -> CommandResult:
    return CommandResult(Text(f"✓ {message}", style="green"))


def _info(message: str) -> CommandResult:
    return CommandResult(Text(message, style="dim"))


def _error(message: str) -> CommandResult:
    return CommandResult(Text(f"✗ {message}", style="red"))
