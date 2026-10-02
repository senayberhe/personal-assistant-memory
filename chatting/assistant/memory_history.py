from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryVersion:
    """
    Represents one historical version of a memory.
    """

    memory_id: str

    version: int

    content: str

    created_at: datetime

    recorded_at: datetime

    memory_key: str | None = None