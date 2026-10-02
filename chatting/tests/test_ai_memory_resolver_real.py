from datetime import datetime
from unittest.mock import MagicMock

from assistant.ai_memory_resolver import (
    AIMemoryResolver,
)
from assistant.memory_model import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_schema import (
    AIResolution,
    AIMemoryResolution,
)


def test_ai_resolver_uses_structured_output():

    settings = MagicMock()

    settings.openai_api_key = "test-key"
    settings.api_timeout = 30
    settings.model = "test-model"

    resolver = AIMemoryResolver(
        settings=settings
    )

    parsed_result = AIMemoryResolution(
        resolution=AIResolution.CONTRADICT,
        confidence=0.96,
        reason=(
            "The new preference conflicts "
            "with the existing preference."
        ),
    )

    resolver.client = MagicMock()

    resolver.client.responses.parse.return_value = (
        MagicMock(
            output_parsed=parsed_result
        )
    )

    memory = Memory(
        id="memory-1",
        content="I prefer Python.",
        created_at=datetime.now(),
    )

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=memory,
    )

    assert (
        result.resolution
        == MemoryResolution.CONTRADICT
    )

    assert result.confidence == 0.96

    resolver.client.responses.parse.assert_called_once()

def make_resolver(parsed_result=None, error=None):
    from unittest.mock import MagicMock

    client = MagicMock()

    if error is not None:
        client.responses.parse.side_effect = error
    else:
        client.responses.parse.return_value = MagicMock(
            output_parsed=parsed_result
        )

    settings = MagicMock()
    settings.model = "test-model"

    return AIMemoryResolver(settings=settings, client=client)


def test_api_error_becomes_service_error():
    import pytest
    from openai import OpenAIError

    from assistant.errors import ServiceError

    resolver = make_resolver(error=OpenAIError("network down"))

    memory = Memory(id="1", content="I prefer Python.", created_at=datetime.now())

    with pytest.raises(ServiceError):
        resolver.resolve("I prefer Rust.", memory)


def test_create_with_existing_memory_is_treated_as_unrelated():
    resolver = make_resolver(
        AIMemoryResolution(
            resolution=AIResolution.CREATE,
            confidence=0.9,
            reason="Different topic.",
        )
    )

    memory = Memory(id="1", content="I prefer Python.", created_at=datetime.now())

    result = resolver.resolve("My favorite color is blue.", memory)

    assert result.resolution == MemoryResolution.UNRELATED


def test_no_existing_memory_skips_the_api():
    resolver = make_resolver()

    result = resolver.resolve("I prefer Python.", None)

    assert result.resolution == MemoryResolution.CREATE
    resolver.client.responses.parse.assert_not_called()


def test_memory_manager_uses_ai_resolver():
    from assistant.in_memory_store import InMemoryStore
    from assistant.memory_manager import MemoryManager
    from tests.fakes.memory_confirmation import FakeMemoryConfirmation

    resolver = make_resolver(
        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            confidence=0.95,
            reason="Refines the preference.",
        )
    )

    confirmation = FakeMemoryConfirmation(approved=False)

    manager = MemoryManager(
        store=InMemoryStore(),
        retriever=None,
        resolver=resolver,
        confirmation=confirmation,
    )

    manager.upsert("I prefer Python.", memory_key="lang")
    updated = manager.upsert("I prefer Python 3.13.", memory_key="lang")

    # High-confidence UPDATE: applied without asking.
    assert updated.content == "I prefer Python 3.13."
    assert updated.version == 2
    assert confirmation.messages == []
