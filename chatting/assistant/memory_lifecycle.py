from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from assistant.memory_model import Memory


class MemoryLifecycle:
    """
    Handles the lifecycle rules for memories.

    Responsibilities:
    - Determine whether a memory has expired.
    - Filter out expired memories.
    - Identify memories that should be cleaned up.
    """

    @staticmethod
    def is_expired(
        memory: Memory,
        now: datetime | None = None,
    ) -> bool:
        """
        Return True if the memory has expired.

        A memory with no expiration date never expires.
        """

        if memory.expires_at is None:
            return False

        if now is None:
            now = datetime.now(
                memory.expires_at.tzinfo
            )

        return now >= memory.expires_at

    @classmethod
    def filter_active(
        cls,
        memories: list[Memory],
        now: datetime | None = None,
    ) -> list[Memory]:
        """
        Return only memories that have not expired.
        """

        return [
            memory
            for memory in memories
            if not cls.is_expired(
                memory,
                now=now,
            )
        ]

    @staticmethod
    def cleanup_expired(
        memories: list[Memory],
        now: datetime | None = None,
    ) -> list[str]:
        """
        Return the IDs of memories that have expired.

        This method does not delete anything.
        The caller decides what to do with those IDs.
        """

        return [
            memory.id
            for memory in memories
            if MemoryLifecycle.is_expired(
                memory,
                now=now,
            )
        ]