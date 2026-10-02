from abc import ABC, abstractmethod

from assistant.memory.retrieval.candidate import MemoryCandidate


class MemoryCandidateRetriever(ABC):
    """
    Finds memories that may be relevant to a new
    memory.
    """

    @abstractmethod
    def retrieve_candidates(
        self,
        query: str,
        candidate_limit: int = 10,
    ) -> list[MemoryCandidate]:
        """
        Retrieve relevant memory candidates.
        """
        pass