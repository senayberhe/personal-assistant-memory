from assistant.memory.events.event import (
    MemoryEvent,
)

from assistant.memory.events.listener import (
    MemoryEventListener,
)

from assistant.memory.events.metrics import (
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