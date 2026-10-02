from abc import ABC, abstractmethod

from assistant.memory_audit import MemoryAuditRecord


class MemoryAuditStore(ABC):
    """
    Storage abstraction for memory audit records.

    """

    @abstractmethod
    def save(
        self,
        record: MemoryAuditRecord
    ) -> None:
        pass

    @abstractmethod
    def get_all(
        self,
    ) -> list[MemoryAuditRecord]:
        pass


    @abstractmethod
    def get_by_memory_id(
        self,
        memory_id: str,
    ) -> list[MemoryAuditRecord]:
        pass
