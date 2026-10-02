from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MemoryAuditRecord:
    """
    Records one memory resolution/update event.

    The record describes an application decision.
    It does not execute the decision.
    """

    record_id: str
    created_at: datetime

    new_content: str

    resolution: str
    action: str

    target_memory_id: str | None

    confidence: float
    reason: str

    similarity: float | None = None
    ranking_score: float | None = None

    confirmation_required: bool = False
    confirmed: bool = False

    success: bool = False
    error: str | None = None

    previous_version: int | None = None
    resulting_version: int | None = None