import logging

from assistant.memory_event import MemoryEvent
from assistant.memory_event_listener import (
    MemoryEventListener,
)


logger = logging.getLogger(__name__)


class MemoryEventPublisher:
    """
    Publishes memory events to registered listeners.
    """

    def __init__(
        self,
        listeners: list[
            MemoryEventListener
        ] | None = None,
    ):
        self.listeners = (
            list(listeners)
            if listeners is not None
            else []
        )

    def subscribe(
        self,
        listener: MemoryEventListener,
    ) -> None:
        self.listeners.append(listener)

    def publish(
        self,
        event: MemoryEvent,
    ) -> None:

        for listener in self.listeners:
            try:
                listener.handle(event)

            except Exception:
                logger.exception(
                    "Memory event listener failed. "
                    "listener=%s event=%s",
                    type(listener).__name__,
                    event.event_type,
                )