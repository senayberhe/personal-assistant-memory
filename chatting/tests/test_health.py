from assistant.health import (
    HealthChecker,
    HealthCheckResult,
)


def test_healthy_check():

    def check():

        return HealthCheckResult(
            name="test",
            healthy=True,
            message="Everything is okay.",
        )

    checker = HealthChecker(
        checks=[check]
    )

    assert checker.is_healthy() is True


def test_unhealthy_check():

    def check():

        return HealthCheckResult(
            name="test",
            healthy=False,
            message="Something is wrong.",
        )

    checker = HealthChecker(
        checks=[check]
    )

    assert checker.is_healthy() is False