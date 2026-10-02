from assistant.memory.model import Memory
from assistant.memory.resolution.result import (
    MemoryResolutionResult,
)
from assistant.memory.resolution.types import (
    MemoryResolution,
)
from assistant.memory.retrieval.candidate import (
    MemoryCandidate,
)


class MemoryResolver:
    """
    Rule-based memory resolver.

    This resolver is deterministic and acts as the
    fallback when the AI resolver is unavailable.
    """

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None = None,
        candidates: list[MemoryCandidate] | None = None,
    ) -> MemoryResolutionResult:

        if not new_content.strip():
            raise ValueError(
                "New memory content cannot be empty."
            )

        if candidates is None:
            candidates = []

        if not candidates and existing_memory is not None:
            candidates = [
                MemoryCandidate(
                    memory=existing_memory,
                    similarity=1.0,
                    ranking_score=1.0,
                )
            ]

        if not candidates:
            return MemoryResolutionResult(
                resolution=MemoryResolution.CREATE,
                confidence=1.0,
                reason=(
                    "No existing memory was found."
                ),
                target_memory_id=None,
            )

        best_candidate = candidates[0]

        existing = best_candidate.memory

        normalized_new = self._normalize(
            new_content
        )

        normalized_existing = self._normalize(
            existing.content
        )

        if normalized_new == normalized_existing:
            return MemoryResolutionResult(
                resolution=MemoryResolution.IGNORE,
                confidence=1.0,
                reason=(
                    "The new memory is identical "
                    "to the existing memory."
                ),
                target_memory_id=existing.id,
            )

        if self._is_contradiction(
            normalized_new,
            normalized_existing,
        ):
            return MemoryResolutionResult(
                resolution=MemoryResolution.CONTRADICT,
                confidence=0.98,
                reason=(
                    "The new memory directly "
                    "contradicts the existing memory."
                ),
                target_memory_id=existing.id,
            )

        if self._is_related(
            normalized_new,
            normalized_existing,
        ):
            return MemoryResolutionResult(
                resolution=MemoryResolution.UPDATE,
                confidence=0.75,
                reason=(
                    "The new memory appears "
                    "related to the existing memory."
                ),
                target_memory_id=existing.id,
            )

        return MemoryResolutionResult(
            resolution=MemoryResolution.UNRELATED,
            confidence=0.90,
            reason=(
                "The new memory does not appear "
                "related to the existing memory."
            ),
            target_memory_id=None,
        )

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        return " ".join(
            text.strip().lower().split()
        )

    @staticmethod
    def _is_contradiction(
        new_content: str,
        existing_content: str,
    ) -> bool:

        contradiction_pairs = [
            (
                "i prefer ",
                "i don't prefer ",
            ),
            (
                "i don't prefer ",
                "i prefer ",
            ),
            (
                "i like ",
                "i don't like ",
            ),
            (
                "i don't like ",
                "i like ",
            ),
            (
                "i use ",
                "i don't use ",
            ),
            (
                "i don't use ",
                "i use ",
            ),
        ]

        for positive, negative in (
            contradiction_pairs
        ):
            if (
                new_content.startswith(positive)
                and existing_content.startswith(
                    negative
                )
            ):
                new_value = new_content[
                    len(positive):
                ]

                existing_value = (
                    existing_content[
                        len(negative):
                    ]
                )

                if new_value == existing_value:
                    return True

        return False

    @staticmethod
    def _is_related(
        new_content: str,
        existing_content: str,
    ) -> bool:

        new_words = set(
            new_content.split()
        )

        existing_words = set(
            existing_content.split()
        )

        if not new_words or not existing_words:
            return False

        overlap = (
            len(
                new_words
                & existing_words
            )
            / min(
                len(new_words),
                len(existing_words),
            )
        )

        return overlap >= 0.50