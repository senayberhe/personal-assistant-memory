from dataclasses import dataclass

from assistant.memory_resolution import (
    MemoryResolution,
)


@dataclass(frozen=True)
class MemoryPolicyDecision:
    """
    Describes what the application should do
    after resolving a memory relationship.
    """

    resolution: MemoryResolution
    action: str
    requires_confirmation: bool
    allowed: bool
    reason: str


class MemoryPolicy:
    """
    Determines what should happen after a memory
    relationship has been resolved.

    The resolver answers:

        "What is this memory?"

    The policy answers:

        "What should we do with it?"

    The policy does NOT modify memory storage.
    """

    CONFIDENCE_THRESHOLD = 0.80

    def decide(
        self,
        resolution: MemoryResolution,
        confidence: float = 1.0,
    ) -> MemoryPolicyDecision:

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "Confidence must be between 0.0 and 1.0."
            )

        if resolution == MemoryResolution.CREATE:
            return MemoryPolicyDecision(
                resolution=resolution,
                action="create",
                requires_confirmation=False,
                allowed=True,
                reason=(
                    "No existing memory was found."
                ),
            )

        if resolution == MemoryResolution.IGNORE:
            return MemoryPolicyDecision(
                resolution=resolution,
                action="ignore",
                requires_confirmation=False,
                allowed=True,
                reason=(
                    "The new memory is identical "
                    "to the existing memory."
                ),
            )

        if resolution == MemoryResolution.UPDATE:

            if (
                confidence
                < self.CONFIDENCE_THRESHOLD
            ):
                return MemoryPolicyDecision(
                    resolution=resolution,
                    action="update",
                    requires_confirmation=True,
                    allowed=True,
                    reason=(
                        "The relationship is "
                        "uncertain, so confirmation "
                        "is required before updating "
                        "the memory."
                    ),
                )

            return MemoryPolicyDecision(
                resolution=resolution,
                action="update",
                requires_confirmation=False,
                allowed=True,
                reason=(
                    "The new memory is sufficiently "
                    "related to the existing memory."
                ),
            )

        if resolution == MemoryResolution.CONTRADICT:
            return MemoryPolicyDecision(
                resolution=resolution,
                action="update",
                requires_confirmation=True,
                allowed=True,
                reason=(
                    "The new memory contradicts "
                    "the existing memory."
                ),
            )

        if resolution == MemoryResolution.UNRELATED:
            return MemoryPolicyDecision(
                resolution=resolution,
                action="create",
                requires_confirmation=False,
                allowed=True,
                reason=(
                    "The new memory is unrelated "
                    "to the existing memory."
                ),
            )

        raise ValueError(
            f"Unsupported memory resolution: "
            f"{resolution}"
        )