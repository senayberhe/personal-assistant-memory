from assistant.chroma_retriever import ChromaRetriever
from assistant.memory_candidate import MemoryCandidate
from assistant.memory_candidate_retriever import (
    MemoryCandidateRetriever,
)


class ChromaMemoryCandidateRetriever(
    MemoryCandidateRetriever
):
    """
    Retrieves semantic memory candidates using
    the existing Chroma retriever.
    """

    def __init__(
        self,
        retriever: ChromaRetriever,
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