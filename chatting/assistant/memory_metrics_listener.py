from assistant.memory_event import (
    MemoryEvent,
)

from assistant.memory_event_listener import (
    MemoryEventListener,
)

from assistant.memory_metrics import (
    MemoryMetrics,
)


class MemoryMetricsListener(
    MemoryEventListener
):
    """
    Updates memory metrics from lifecycle events.
    """

    def __init__(
        self,
        metrics: MemoryMetrics,
    ):
        self.metrics = metrics

    def handle(
        self,
        event: MemoryEvent,
    ) -> None:

        self.metrics.record(
            action=event.action,
            success=event.success,
        )