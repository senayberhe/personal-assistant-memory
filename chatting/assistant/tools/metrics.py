from dataclasses import dataclass, field


@dataclass
class ToolMetrics:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency: float = 0.0

    @property
    def average_latency(self) -> float:
        if self.calls == 0:
            return 0.0

        return (
            self.total_latency / self.calls
        )

@dataclass
class Metrics:
    tools: dict[str, ToolMetrics] = field(default_factory=dict)

    def record_success(
            self,
            tool_name: str,
            latency: float
    ) -> None:
        metrics = self.tools.setdefault(
            tool_name,
            ToolMetrics()
        )
        metrics.calls += 1
        metrics.successes += 1
        metrics.total_latency += latency

    def record_failure(
            self,
            tool_name: str,
            latency: float
    ) -> None:
        metrics = self.tools.setdefault(
            tool_name,
            ToolMetrics()
        )
        metrics.calls += 1
        metrics.failures += 1
        metrics.total_latency += latency

    def get(
        self,
        tool_name: str,
    ) -> ToolMetrics:
        return self.tools.setdefault(
            tool_name,
            ToolMetrics()
        )