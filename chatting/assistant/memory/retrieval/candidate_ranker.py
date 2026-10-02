from assistant.memory.ranking import (
    calculate_final_score,
    calculate_recency,
)
from assistant.memory.retrieval.candidate import MemoryCandidate


class MemoryCandidateRanker:
    """
    Ranks memory candidates using:

    - semantic similarity
    - memory importance
    - memory recency
    """

    def __init__(
        self,
        recency_decay_days: float = 30.0,
    ):
        if recency_decay_days <= 0:
            raise ValueError(
                "recency_decay_days must be greater than zero."
            )

        self.recency_decay_days = (
            recency_decay_days
        )

    def rank(
        self,
        candidates: list[MemoryCandidate],
        top_k: int | None = None,
    ) -> list[MemoryCandidate]:
        """
        Rank candidates from highest relevance
        to lowest relevance.

        If top_k is provided, return only the
        top_k candidates.
        """

        if top_k is not None and top_k <= 0:
            return []

        ranked_candidates = []

        for candidate in candidates:

            recency = calculate_recency(
                created_at=candidate.memory.created_at,
                decay_days=self.recency_decay_days,
            )

            ranking_score = calculate_final_score(
                similarity=candidate.similarity,
                importance=candidate.memory.importance,
                recency=recency,
            )

            ranked_candidates.append(
                MemoryCandidate(
                    memory=candidate.memory,
                    similarity=candidate.similarity,
                    ranking_score=ranking_score,
                )
            )

        ranked_candidates.sort(
            key=lambda candidate: candidate.ranking_score,
            reverse=True,
        )

        if top_k is not None:
            return ranked_candidates[:top_k]

        return ranked_candidates