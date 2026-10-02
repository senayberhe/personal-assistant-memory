from dataclasses import dataclass

from assistant.memory_resolution import (
    MemoryResolution,
)


@dataclass(frozen=True)
class MemoryResolutionResult:
    """
    Describes the relationship between a new memory
    and an existing memory.

    Includes:

    - resolution
    - confidence
    - reason
    """

    resolution: MemoryResolution
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Confidence must be between 0.0 and 1.0."
            )

        if not self.reason.strip():
            raise ValueError(
                "Resolution reason cannot be empty."
            )