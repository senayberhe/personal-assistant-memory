from enum import Enum

from pydantic import BaseModel, Field

from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)


class AIResolution(str, Enum):
    """
    Possible relationships between a new memory
    and existing memory candidates.
    """

    CREATE = "CREATE"
    IGNORE = "IGNORE"
    UPDATE = "UPDATE"
    CONTRADICT = "CONTRADICT"
    UNRELATED = "UNRELATED"


class AIMemoryResolution(BaseModel):
    """
    Structured response returned by the AI resolver.
    """

    resolution: AIResolution = Field(
        description=(
            "Relationship between the new memory "
            "and candidate memories."
        )
    )

    target_memory_id: str | None = Field(
        default=None,
        description=(
            "ID of the existing memory affected "
            "by the resolution. Null when no "
            "existing memory should be modified."
        ),
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the classification."
        ),
    )

    reason: str = Field(
        min_length=1,
        description=(
            "Short factual explanation."
        ),
    )

    def to_domain_result(
        self,
    ) -> MemoryResolutionResult:
        """
        Convert the AI response into the application's
        domain representation.
        """

        return MemoryResolutionResult(
            # AI labels match the enum NAMES ("CREATE"),
            # not its values ("create").
            resolution=MemoryResolution[
                self.resolution.value
            ],
            confidence=self.confidence,
            reason=self.reason,
            target_memory_id=(
                self.target_memory_id
            ),
        )