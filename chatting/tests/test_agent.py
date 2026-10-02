from unittest.mock import MagicMock


class FakeAgent:

    def __init__(
        self,
        executor,
    ):
        self.executor = executor

    def run(
        self,
        text: str,
    ) -> str:

        if "search" in text.lower():

            return self.executor.execute(
                "search_google",
                {
                    "query": "Python"
                },
            )

        return "I don't understand."


def test_agent_search():

    executor = MagicMock()

    executor.execute.return_value = (
        "Search completed."
    )

    agent = FakeAgent(
        executor
    )

    result = agent.run(
        "Search for Python"
    )

    assert result == (
        "Search completed."
    )

    executor.execute.assert_called_once_with(
        "search_google",
        {
            "query": "Python"
        },
    )

# --------------------------------------------------
# VoiceAgent
# --------------------------------------------------

import json
from types import SimpleNamespace

import pytest

from assistant.agent import VoiceAgent
from assistant.embeddings import SimpleEmbeddingService
from assistant.errors import AgentError, PermissionDeniedError, ToolError
from assistant.in_memory_retriever import InMemoryRetriever
from assistant.in_memory_store import InMemoryStore
from assistant.memory import MemoryManager
from assistant.memory_extractor import MemoryExtractor


def text_response(text):
    return SimpleNamespace(output=[], output_text=text)


def tool_response(name, arguments, call_id="call_1"):
    return SimpleNamespace(
        output=[
            SimpleNamespace(
                type="function_call",
                name=name,
                arguments=json.dumps(arguments),
                call_id=call_id,
            )
        ],
        output_text="",
    )


def make_agent(responses, executor=None, **kwargs):

    client = MagicMock()
    client.responses.create.side_effect = responses

    settings = SimpleNamespace(model="test-model", max_agent_steps=3)

    agent = VoiceAgent(
        executor=executor or MagicMock(),
        tool_definitions=[],
        settings=settings,
        client=client,
        **kwargs,
    )

    return agent, client


def test_voice_agent_returns_text_reply():

    agent, _ = make_agent([text_response("Hello!")])

    assert agent.run("hi") == "Hello!"
    assert agent.conversation.get_messages()[-1] == {
        "role": "assistant",
        "content": "Hello!",
    }


def test_voice_agent_executes_tool_calls():

    executor = MagicMock()
    executor.execute.return_value = "Searching Google for Python."

    agent, client = make_agent(
        [
            tool_response("search_google", {"query": "Python"}),
            text_response("I searched for Python."),
        ],
        executor=executor,
    )

    assert agent.run("search for Python") == "I searched for Python."

    executor.execute.assert_called_once_with(
        "search_google",
        {"query": "Python"},
    )

    second_input = client.responses.create.call_args.kwargs["input"]

    assert second_input[-1] == {
        "type": "function_call_output",
        "call_id": "call_1",
        "output": "Searching Google for Python.",
    }


def test_voice_agent_reports_tool_errors_to_model():

    executor = MagicMock()
    executor.execute.side_effect = ToolError("Tool 'x' failed.")

    agent, client = make_agent(
        [
            tool_response("x", {}),
            text_response("Sorry, that failed."),
        ],
        executor=executor,
    )

    assert agent.run("do x") == "Sorry, that failed."

    second_input = client.responses.create.call_args.kwargs["input"]
    assert second_input[-1]["output"].startswith("Error:")


def test_voice_agent_propagates_permission_denied():

    executor = MagicMock()
    executor.execute.side_effect = PermissionDeniedError("no")

    agent, _ = make_agent(
        [tool_response("open_terminal", {})],
        executor=executor,
    )

    with pytest.raises(PermissionDeniedError):
        agent.run("open terminal")


def test_voice_agent_stops_after_max_steps():

    agent, _ = make_agent(
        [tool_response("open_chrome", {})] * 3,
    )

    with pytest.raises(AgentError):
        agent.run("loop forever")


def test_voice_agent_saves_and_recalls_memories():

    store = InMemoryStore()

    memory_manager = MemoryManager(
        store=store,
        retriever=InMemoryRetriever(
            memory_store=store,
            embedding_service=SimpleEmbeddingService(),
        ),
    )

    agent, client = make_agent(
        [text_response("Noted."), text_response("Noted.")],
        memory_manager=memory_manager,
        memory_extractor=MemoryExtractor(),
    )

    agent.run("Remember that I like dark mode")
    agent.run("Remember that I like dark mode")

    # Saved once; the duplicate is skipped.
    assert len(store.get_all()) == 1

    instructions = client.responses.create.call_args.kwargs["input"][0]
    assert "I like dark mode" in instructions["content"]
