from assistant.memory_policy import MemoryPolicy
from assistant.memory_resolution import (
    MemoryResolution,
)


def test_low_confidence_update_requires_confirmation():

    policy = MemoryPolicy()

    decision = policy.decide(
        resolution=MemoryResolution.UPDATE,
        confidence=0.40,
    )

    assert decision.action == "update"
    assert decision.requires_confirmation is True
    assert decision.allowed is True


def test_high_confidence_update_does_not_require_confirmation():

    policy = MemoryPolicy()

    decision = policy.decide(
        resolution=MemoryResolution.UPDATE,
        confidence=0.95,
    )

    assert decision.action == "update"
    assert decision.requires_confirmation is False
    assert decision.allowed is True


def test_contradiction_always_requires_confirmation():

    policy = MemoryPolicy()

    decision = policy.decide(
        resolution=MemoryResolution.CONTRADICT,
        confidence=1.0,
    )

    assert decision.requires_confirmation is True