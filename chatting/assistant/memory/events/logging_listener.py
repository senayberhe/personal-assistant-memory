import logging

from assistant.memory.events.event import (
    MemoryEvent,
)
from assistant.memory.events.listener import (
    MemoryEventListener,
)

logger = logging.getLogger(
    "assistant.memory"
)


class MemoryLoggingListener(
    MemoryEventListener
):
    """
    Writes memory lifecycle events to
    the application logger.
    """

    def handle(
        self,
        event: MemoryEvent,
    ) -> None:

        logger.info(
            "Memory event: "
            "type=%s "
            "memory_id=%s "
            "action=%s "
            "success=%s "
            "previous_version=%s "
            "resulting_version=%s",
            event.event_type,
            event.memory_id,
            event.action,
            event.success,
            event.previous_version,
            event.resulting_version,
        )