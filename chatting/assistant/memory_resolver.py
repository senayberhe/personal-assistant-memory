from assistant.memory_model import Memory
from assistant.memory_resolution import MemoryResolution


class MemoryResolver:
    """
    Determines what should happen when a new memory
    is compared with an existing memory.
    """

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None,
    ) -> MemoryResolution:

        if existing_memory is None:
            return MemoryResolution.CREATE

        normalized_new = (
            new_content
            .strip()
            .lower()
        )

        normalized_existing = (
            existing_memory.content
            .strip()
            .lower()
        )

        if normalized_new == normalized_existing:
            return MemoryResolution.IGNORE

        return MemoryResolution.UPDATE