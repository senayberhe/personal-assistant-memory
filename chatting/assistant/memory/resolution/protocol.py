from typing import Protocol

from assistant.memory.model import Memory
from assistant.memory.resolution.result import (
    MemoryResolutionResult,
)
from assistant.memory.retrieval.candidate import (
    MemoryCandidate,
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