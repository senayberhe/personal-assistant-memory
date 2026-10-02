from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Memory:
    """
    Represents a single long-term memory.

    A memory contains information plus metadata used
    for retrieval, ranking, expiration, and versioning.
    """

    id: str

    content: str

    created_at: datetime

    memory_type: str = "general"

    importance: float = 0.5

    source: str = "conversation"

    metadata: dict = field(
        default_factory=dict
    )

    expires_at: datetime | None = None

    memory_key: str | None = None

    version: int = 1


def validate_importance(
    importance: float,
) -> float:
    """
    Validate memory importance.

    Importance must be between 0.0 and 1.0.
    """

    if not 0.0 <= importance <= 1.0:
        raise ValueError(
            "Memory importance must be between 0.0 and 1.0."
        )

    return importance