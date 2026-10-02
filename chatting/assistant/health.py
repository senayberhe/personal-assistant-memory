from dataclasses import dataclass


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    healthy: bool
    message: str


class HealthChecker:
    def __init__(self, checks=None):
        self.checks = checks or []

    def run(self) -> list[HealthCheckResult]:
        results = []

        for check in self.checks:
            results.append(check())

        return results

    def is_healthy(self) -> bool:
        results = self.run()

        return all(
            result.healthy
            for result in results
        )