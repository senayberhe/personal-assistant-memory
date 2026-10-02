import pytest

from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_schema import (
    AIResolution,
    AIMemoryResolution,
)


def test_valid_resolution():

    result = AIMemoryResolution(
        resolution=AIResolution.CONTRADICT,
        confidence=0.95,
        reason="The preferences conflict.",
    )

    assert (
        result.resolution
        == AIResolution.CONTRADICT
    )

    assert result.confidence == 0.95


def test_confidence_cannot_exceed_one():

    with pytest.raises(ValueError):

        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            confidence=1.5,
            reason="Invalid confidence.",
        )


def test_confidence_cannot_be_negative():

    with pytest.raises(ValueError):

        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            confidence=-0.1,
            reason="Invalid confidence.",
        )


def test_empty_reason_is_rejected():

    with pytest.raises(ValueError):

        AIMemoryResolution(
            resolution=AIResolution.UPDATE,
            confidence=0.8,
            reason="",
        )


def test_domain_conversion():

    result = AIMemoryResolution(
        resolution=AIResolution.CONTRADICT,
        confidence=0.95,
        reason="The preferences conflict.",
    )

    domain_result = (
        result.to_domain_result()
    )

    assert (
        domain_result.resolution
        == MemoryResolution.CONTRADICT
    )

    assert domain_result.confidence == 0.95