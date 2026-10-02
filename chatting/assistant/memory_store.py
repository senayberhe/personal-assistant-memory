from abc import ABC, abstractmethod

from assistant.memory_model import Memory


class MemoryStore(ABC):

    @abstractmethod
    def save(
        self,
        memory: Memory,
    ) -> None:
        pass

    @abstractmethod
    def get_all(
        self,
    ) -> list[Memory]:
        pass

    @abstractmethod
    def delete(
        self,
        memory_id: str,
    ) -> None:
        pass

    @abstractmethod
    def find_by_key(
        self,
        memory_key: str,
    ) -> list[Memory]:
        pass