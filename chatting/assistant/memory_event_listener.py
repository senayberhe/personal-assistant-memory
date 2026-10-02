from abc import ABC, abstractmethod
from assistant.memory_event import MemoryEvent


class MemoryEventListener(ABC):
    """
    Abstract base class for handling memory events.
    Implementations should define how to respond to different types of memory events.
    """

    @abstractmethod
    def handle(
        self,
        event: MemoryEvent,
    ) -> None:
        pass