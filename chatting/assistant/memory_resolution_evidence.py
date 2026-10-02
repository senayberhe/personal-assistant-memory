from dataclasses import dataclass


@dataclass(frozen=True)
class ResolutionEvidence:
    """
    Evidence explaining why a memory resolution
    was selected.
    """

    target_memory_id: str | None
    similarity: float | None
    ranking_score: float | None
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Confidence must be between 0.0 and 1.0."
            )

        if self.similarity is not None:
            if not 0.0 <= self.similarity <= 1.0:
                raise ValueError(
                    "Similarity must be between 0.0 and 1.0."
                )

        if self.ranking_score is not None:
            if self.ranking_score < 0.0:
                raise ValueError(
                    "Ranking score cannot be negative."
                )

        if not self.reason.strip():
            raise ValueError(
                "Evidence reason cannot be empty."
            )