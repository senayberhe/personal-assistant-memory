from typing import Protocol

from assistant.memory_model import Memory
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)


class MemoryResolverProtocol(Protocol):
    """
    Contract for memory relationship resolvers.

    Both the rule-based MemoryResolver and the
    AIMemoryResolver satisfy it.
    """

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None,
    ) -> MemoryResolutionResult:
        ...
