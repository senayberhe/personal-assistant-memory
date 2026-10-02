from abc import ABC, abstractmethod
from dataclasses import dataclass

from assistant.memory_model import Memory


@dataclass
class RetrievedMemory:
    memory: Memory
    score: float


class Retriever(ABC):

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[Memory]:
        return [
            item.memory
            for item in self.retrieve_scored(
                query,
                top_k=top_k,
                memory_type=memory_type,
            )
        ]

    @abstractmethod
    def retrieve_scored(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[RetrievedMemory]:
        """Return memories with a similarity score, best first."""
