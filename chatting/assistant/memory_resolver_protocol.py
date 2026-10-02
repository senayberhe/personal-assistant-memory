from typing import Protocol

from assistant.memory_candidate import (
    MemoryCandidate,
)
from assistant.memory_model import Memory
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)


class MemoryResolverProtocol(Protocol):
    """
    Common interface for all memory resolvers.
    """

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None = None,
        candidates: list[MemoryCandidate] | None = None,
    ) -> MemoryResolutionResult:
        ...