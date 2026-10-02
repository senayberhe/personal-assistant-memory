from assistant.memory.retrieval.base import Retriever
from assistant.memory.retrieval.candidate import MemoryCandidate
from assistant.memory.retrieval.candidate_retriever import (
    MemoryCandidateRetriever,
)


class ScoredCandidateRetriever(
    MemoryCandidateRetriever
):
    """
    Turns any Retriever's scored results into memory candidates.

    Works with the Chroma and the in-memory retriever alike.
    """

    def __init__(
        self,
        retriever: Retriever,
    ):
        self.retriever = retriever

    def retrieve_candidates(
        self,
        query: str,
        candidate_limit: int = 10,
    ) -> list[MemoryCandidate]:

        if not query.strip():
            return []

        if candidate_limit <= 0:
            return []

        # retrieve() returns plain Memory objects;
        # retrieve_scored() includes the similarity.
        results = self.retriever.retrieve_scored(
            query,
            top_k=candidate_limit,
        )

        return [
            MemoryCandidate(
                memory=result.memory,
                similarity=result.score,
                ranking_score=result.score,
            )
            for result in results
        ]