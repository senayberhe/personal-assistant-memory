from abc import ABC, abstractmethod

from assistant.memory_history import (
    MemoryVersion,
)


class MemoryHistoryStore(ABC):
    """
    Abstract interface for memory history storage.
    """

    @abstractmethod
    def save_version(
        self,
        version: MemoryVersion,
    ) -> None:
        """
        Save a historical memory version.
        """
        pass

    @abstractmethod
    def get_history(
        self,
        memory_id: str,
    ) -> list[MemoryVersion]:
        """
        Return the version history for a memory.
        """
        pass