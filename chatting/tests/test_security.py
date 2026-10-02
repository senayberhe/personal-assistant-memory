from assistant.security import (
    RiskLevel,
    SecurityPolicy,
)


def test_low_risk_is_allowed():

    policy = SecurityPolicy()

    assert policy.is_allowed(
        RiskLevel.LOW
    )


def test_high_risk_requires_confirmation():

    policy = SecurityPolicy()

    assert policy.requires_confirmation(
        RiskLevel.HIGH
    )


def test_critical_action_is_blocked():

    policy = SecurityPolicy()

    assert not policy.is_allowed(
        RiskLevel.CRITICAL
    )