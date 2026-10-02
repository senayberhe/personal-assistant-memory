import pytest

from assistant.memory.resolution.types import (
    MemoryResolution,
)
from assistant.memory.resolution.schema import (
    AIResolution,
    AIMemoryResolution,
)


def test_valid_resolution():

    result = AIMemoryResolution(
        resolution=AIResolution.CONTRADICT,
        target_memory_id="memory-123",
        confidence=0.95,
        reason="The preferences conflict.",
    )

    assert (
        result.resolution
        == AIResolution.CONTRADICT
    )

    assert (
        result.target_memory_id
        == "memory-123"
    )

    assert result.confidence == 0.95


def test_create_allows_no_target():

    result = AIMemoryResolution(
        resolution=AIResolution.CREATE,
        target_memory_id=None,
        confidence=0.95,
        reason="No related memory exists.",
    )

    assert result.target_memory_id is None


def test_confidence_cannot_exceed_one():

    with pytest.raises(ValueError):

        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            target_memory_id="memory-1",
            confidence=1.5,
            reason="Invalid confidence.",
        )


def test_confidence_cannot_be_negative():

    with pytest.raises(ValueError):

        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            target_memory_id="memory-1",
            confidence=-0.1,
            reason="Invalid confidence.",
        )


def test_empty_reason_is_rejected():

    with pytest.raises(ValueError):

        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            target_memory_id="memory-1",
            confidence=0.8,
            reason="",
        )


def test_domain_conversion():

    result = AIMemoryResolution(
        resolution=AIResolution.CONTRADICT,
        target_memory_id="memory-1",
        confidence=0.95,
        reason="The preferences conflict.",
    )

    domain_result = result.to_domain_result()

    assert (
        domain_result.resolution
        == MemoryResolution.CONTRADICT
    )

    assert domain_result.confidence == 0.95