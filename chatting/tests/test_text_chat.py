from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from assistant.errors import AgentError, PermissionDeniedError
from assistant.interfaces.commands import ChatCommands
from assistant.interfaces.prompter import RichPrompter
from assistant.interfaces.text_chat import TextChat
from assistant.memory import MemoryManager
from assistant.memory.embeddings import SimpleEmbeddingService
from assistant.memory.events.metrics import MemoryMetrics
from assistant.memory.history.in_memory import InMemoryHistoryStore
from assistant.memory.retrieval.in_memory import InMemoryRetriever
from assistant.memory.retrieval.scored_candidate_retriever import (
    ScoredCandidateRetriever,
)
from assistant.memory.storage.in_memory import InMemoryStore
from assistant.tools.metrics import Metrics


def make_manager():
    store = InMemoryStore()
    retriever = InMemoryRetriever(
        memory_store=store,
        embedding_service=SimpleEmbeddingService(),
    )

    return MemoryManager(
        store=store,
        retriever=retriever,
        history_store=InMemoryHistoryStore(),
        candidate_retriever=ScoredCandidateRetriever(retriever),
        confirmation=MagicMock(confirm=MagicMock(return_value=True)),
    )


def make_commands(manager=None, confirm=lambda question: True, **kwargs):
    return ChatCommands(
        memory_manager=manager or make_manager(),
        reset_conversation=kwargs.pop("reset", MagicMock()),
        confirm=confirm,
        **kwargs,
    )


def render(result) -> str:
    console = Console(file=StringIO(), width=120)
    console.print(result.output)
    return console.file.getvalue()


# --------------------------------------------------
# Commands
# --------------------------------------------------


def test_help_lists_commands():
    output = render(make_commands().handle("/help"))

    for command in ["/memories", "/remember", "/forget", "/history", "/quit"]:
        assert command in output


def test_remember_then_list_memories():
    commands = make_commands()

    assert "Saved as" in render(commands.handle("/remember I prefer Python"))
    assert "Already remembered" in render(
        commands.handle("/remember I prefer Python")
    )

    output = render(commands.handle("/memories"))

    assert "I prefer Python" in output
    assert "Saved memories (1)" in output


def test_search_memories_shows_scores():
    commands = make_commands()
    commands.handle("/remember I prefer Python")

    output = render(commands.handle("/memories python"))

    assert "Score" in output
    assert "I prefer Python" in output


def test_remember_refuses_secrets():
    commands = make_commands()

    output = render(commands.handle("/remember my password is hunter2"))

    assert "Refusing to store sensitive data" in output
    assert "hunter2" not in output


def test_forget_asks_first_and_accepts_id_prefix():
    manager = make_manager()
    memory = manager.remember("I like tea")

    declined = make_commands(manager, confirm=lambda question: False)
    assert "Kept" in render(declined.handle(f"/forget {memory.id[:6]}"))
    assert manager.get_all() == [memory]

    accepted = make_commands(manager, confirm=lambda question: True)
    assert "Forgot" in render(accepted.handle(f"/forget {memory.id[:6]}"))
    assert manager.get_all() == []


def test_ambiguous_or_unknown_ids_are_explained():
    manager = make_manager()
    first = manager.remember("First")
    second = manager.remember("Second")
    first.id, second.id = "abc111", "abc222"

    commands = make_commands(manager)

    assert "No memory with ID" in render(commands.handle("/forget zzzz"))
    assert "matches 2 memories" in render(commands.handle("/forget abc"))
    # An empty prefix is a usage error, not "matches everything".
    assert "Usage" in render(commands.handle("/forget "))
    assert "Usage" in render(commands.handle("/history"))


def test_history_and_restore():
    manager = make_manager()
    memory = manager.remember("I prefer Python")
    manager.update_memory(memory.id, content="I prefer Rust")

    commands = make_commands(manager)

    history = render(commands.handle(f"/history {memory.id}"))
    assert "I prefer Python" in history
    assert "I prefer Rust" in history

    restored = render(commands.handle(f"/restore {memory.id} 1"))
    assert "Restored version 1 as version 3" in restored

    assert "Usage" in render(commands.handle(f"/restore {memory.id} one"))


def test_stats_show_memory_and_tool_metrics():
    memory_metrics = MemoryMetrics()
    memory_metrics.record("create", success=True)

    tool_metrics = Metrics()
    tool_metrics.record_success("search_google", 0.5)

    commands = make_commands(
        memory_metrics=memory_metrics,
        tool_metrics=tool_metrics,
    )

    output = render(commands.handle("/stats"))

    assert "Memories created" in output
    assert "Tool search_google" in output
    assert "1/1 ok" in output


def test_clear_resets_conversation_only():
    reset = MagicMock()
    manager = make_manager()
    manager.remember("I like tea")

    commands = make_commands(manager, reset=reset)

    commands.handle("/clear")

    reset.assert_called_once()
    assert len(manager.get_all()) == 1


@pytest.mark.parametrize("command", ["/quit", "/exit", "/q"])
def test_quit_aliases(command):
    assert make_commands().handle(command).quit


def test_unknown_command():
    assert "Unknown command" in render(make_commands().handle("/dance"))


# --------------------------------------------------
# Chat loop
# --------------------------------------------------


def run_chat(lines, agent=None):
    console = Console(file=StringIO(), width=100, force_terminal=False)
    agent = agent or MagicMock()
    inputs = iter(lines)

    def read_input():
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError from None

    chat = TextChat(
        agent=agent,
        commands=make_commands(),
        prompter=RichPrompter(console),
        console=console,
        read_input=read_input,
    )

    chat.run()

    return console.file.getvalue(), agent


def test_chat_sends_messages_to_agent_and_shows_reply():
    agent = MagicMock()
    agent.run.return_value = "Hello **there**"

    output, agent = run_chat(["hi", "/quit"], agent)

    agent.run.assert_called_once_with("hi")
    assert "Hello there" in output
    assert "Goodbye" in output


def test_commands_do_not_reach_the_agent():
    output, agent = run_chat(["/help", "/quit"])

    agent.run.assert_not_called()
    assert "/memories" in output


def test_errors_are_shown_kindly():
    agent = MagicMock()
    agent.run.side_effect = [
        PermissionDeniedError("no"),
        AgentError("down"),
        RuntimeError("boom"),
    ]

    output, _ = run_chat(["a", "b", "c"], agent)

    assert "Okay, I won't do that." in output
    assert "couldn't reach the language model" in output
    assert "Something unexpected went wrong" in output
    assert "boom" not in output


def test_tool_calls_are_shown():
    agent = MagicMock()

    def run(text):
        agent.on_tool_call("search_google", {"query": "cats"})
        return "Done"

    agent.run.side_effect = run

    output, _ = run_chat(["search cats"], agent)

    assert "search_google(query='cats')" in output


def test_end_of_input_exits_cleanly():
    output, _ = run_chat([])

    assert "Goodbye" in output


def test_prompter_treats_end_of_input_as_no(monkeypatch):
    console = Console(file=StringIO())
    prompter = RichPrompter(console)

    def raise_eof(*args, **kwargs):
        raise EOFError

    monkeypatch.setattr("rich.prompt.Confirm.ask", raise_eof)

    assert prompter.confirm("Run it?") is False


def test_prompter_pauses_spinner_while_asking(monkeypatch):
    console = Console(file=StringIO())
    prompter = RichPrompter(console)
    prompter.active_status = MagicMock()

    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *a, **k: True)

    assert prompter.confirm("Run it?") is True
    prompter.active_status.stop.assert_called_once()
    prompter.active_status.start.assert_called_once()


def test_memory_dates_render():
    manager = make_manager()
    memory = manager.remember("I like tea")
    memory.created_at = datetime(2026, 1, 2)

    output = render(make_commands(manager).handle("/memories"))

    assert "2026-01-02" in output
