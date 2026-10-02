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
    Labels the AI model is allowed to return.

    Using an enum (instead of a plain string) puts the
    allowed values in the JSON schema sent to the model,
    so it cannot answer with an unknown label.
    """

    CREATE = "CREATE"
    IGNORE = "IGNORE"
    UPDATE = "UPDATE"
    CONTRADICT = "CONTRADICT"
    UNRELATED = "UNRELATED"


class AIMemoryResolution(BaseModel):
    """
    Structured output expected from the AI
    memory resolver.
    """

    resolution: AIResolution = Field(
        description=(
            "Memory relationship: CREATE, IGNORE, "
            "UPDATE, CONTRADICT, or UNRELATED."
        )
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
            "Short explanation for the classification."
        ),
    )

    def to_domain_result(
        self,
    ) -> MemoryResolutionResult:
        """
        Convert the AI output into the result type
        used by the rest of the memory system.
        """

        return MemoryResolutionResult(
            resolution=MemoryResolution[
                self.resolution.value
            ],
            confidence=self.confidence,
            reason=self.reason,
        )
