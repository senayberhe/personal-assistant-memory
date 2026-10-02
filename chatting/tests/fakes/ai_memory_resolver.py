from assistant.memory_model import Memory
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)


class FakeMemoryResolver:

    def __init__(
        self,
        result: MemoryResolutionResult,
    ):
        self.result = result
        self.calls = []

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None,
    ) -> MemoryResolutionResult:

        self.calls.append(
            {
                "new_content": new_content,
                "existing_memory": existing_memory,
            }
        )

        return self.result