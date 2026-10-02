from datetime import datetime

from assistant.memory_model import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)
from tests.fakes.ai_memory_resolver import (
    FakeMemoryResolver,
)


def test_fake_resolver_returns_structured_result():

    expected = MemoryResolutionResult(
        resolution=MemoryResolution.CONTRADICT,
        confidence=0.95,
        reason="The preferences conflict.",
    )

    resolver = FakeMemoryResolver(
        result=expected
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

    assert result == expected

    assert len(
        resolver.calls
    ) == 1