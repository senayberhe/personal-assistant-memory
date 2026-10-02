from assistant.memory.history.model import (
    MemoryVersion,
)
from assistant.memory.history.base import (
    MemoryHistoryStore,
)


class InMemoryHistoryStore(
    MemoryHistoryStore
):
    """
    Stores memory history in Python memory.

    Useful for testing.
    """

    def __init__(self):
        self.versions: dict[
            str,
            list[MemoryVersion],
        ] = {}

    def save_version(
        self,
        version: MemoryVersion,
    ) -> None:

        history = self.versions.setdefault(
            version.memory_id,
            [],
        )

        history.append(
            version
        )

    def get_history(
        self,
        memory_id: str,
    ) -> list[MemoryVersion]:

        return list(
            self.versions.get(
                memory_id,
                [],
            )
        )