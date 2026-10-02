from assistant.memory.model import Memory
from assistant.memory.resolution.result import (
    MemoryResolutionResult,
)


class FakeMemoryResolver:

    def __init__(
        self,
        result: MemoryResolutionResult,
    ):
        self.result = result
        self.calls: list[dict] = []

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None = None,
        candidates: list | None = None,
    ) -> MemoryResolutionResult:

        self.calls.append(
            {
                "new_content": new_content,
                "existing_memory": existing_memory,
                "candidates": candidates,
            }
        )

        return self.result