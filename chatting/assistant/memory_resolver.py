from assistant.memory_model import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)


class MemoryResolver:
    """
    Determines how a new memory relates to an
    existing memory.

    The resolver returns a structured result
    containing:

    - resolution
    - confidence
    - reason

    This implementation is intentionally
    rule-based.

    A future AI resolver can implement the
    same interface.
    """

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None,
    ) -> MemoryResolutionResult:

        if not new_content.strip():
            raise ValueError(
                "New memory content cannot be empty."
            )

        if existing_memory is None:
            return MemoryResolutionResult(
                resolution=MemoryResolution.CREATE,
                confidence=1.0,
                reason=(
                    "No existing memory was found."
                ),
            )

        normalized_new = self._normalize(
            new_content
        )

        normalized_existing = self._normalize(
            existing_memory.content
        )

        if normalized_new == normalized_existing:
            return MemoryResolutionResult(
                resolution=MemoryResolution.IGNORE,
                confidence=1.0,
                reason=(
                    "The new memory is identical "
                    "to the existing memory."
                ),
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
            )

        return MemoryResolutionResult(
            resolution=MemoryResolution.UNRELATED,
            confidence=0.90,
            reason=(
                "The new memory does not appear "
                "related to the existing memory."
            ),
        )

    @staticmethod
    def _normalize(text: str) -> str:
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