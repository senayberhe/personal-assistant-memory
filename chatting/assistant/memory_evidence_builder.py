from assistant.memory_candidate import (
    MemoryCandidate,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)
from assistant.memory_resolution_evidence import (
    ResolutionEvidence,
)


class MemoryEvidenceBuilder:
    """
    Converts resolver results and candidates
    into explainable evidence.
    """

    @staticmethod
    def build(
        result: MemoryResolutionResult,
        candidates: list[MemoryCandidate],
    ) -> ResolutionEvidence:

        target = None

        if result.target_memory_id is not None:

            target = next(
                (
                    candidate
                    for candidate in candidates
                    if (
                        candidate.memory.id
                        == result.target_memory_id
                    )
                ),
                None,
            )

        if target is None:

            return ResolutionEvidence(
                target_memory_id=(
                    result.target_memory_id
                ),
                similarity=None,
                ranking_score=None,
                confidence=result.confidence,
                reason=result.reason,
            )

        return ResolutionEvidence(
            target_memory_id=target.memory.id,
            similarity=target.similarity,
            ranking_score=target.ranking_score,
            confidence=result.confidence,
            reason=result.reason,
        )