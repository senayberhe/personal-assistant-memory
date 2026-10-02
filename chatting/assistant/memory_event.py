from dataclasses import dataclass
from datetime import datetime

from assistant.memory_resolution import (
    MemoryResolution,
)


@dataclass(frozen=True)
class MemoryEvent:
    """
    Represents an event that occurred during
    a memory operation.
    """

    event_id: str
    created_at: datetime

    event_type: str

    memory_id: str | None

    resolution: MemoryResolution | None

    action: str

    content: str

    success: bool

    confidence: float | None = None

    reason: str | None = None

    previous_version: int | None = None

    resulting_version: int | None = None

    error: str | None = None