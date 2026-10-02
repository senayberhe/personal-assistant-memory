from assistant.memory_model import Memory
from assistant.memory_store import MemoryStore


class InMemoryStore(MemoryStore):

    def __init__(self):
        self.memories: dict[str, Memory] = {}

    def save(self, memory: Memory) -> None:
        self.memories[memory.id] = memory

    def get_all(self) -> list[Memory]:
        return list(self.memories.values())

    def delete(self, memory_id: str) -> None:
        self.memories.pop(memory_id, None)

    def find_by_key(self, memory_key: str) -> list[Memory]:
        return [
            memory
            for memory in self.memories.values()
            if memory.memory_key == memory_key
        ]
