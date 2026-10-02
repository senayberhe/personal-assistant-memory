import pytest

from assistant.memory import Memory
from assistant.memory.storage.base import MemoryStore


class FakeMemoryStore(MemoryStore):

    def __init__(self):
        self.memories = {}

    def save(
        self,
        memory: Memory,
    ) -> None:
        self.memories[memory.id] = memory

    def get_all(
        self,
    ) -> list[Memory]:
        return list(
            self.memories.values()
        )

    def delete(
        self,
        memory_id: str,
    ) -> None:
        self.memories.pop(
            memory_id,
            None,
        )

    def find_by_key(
        self,
        memory_key: str,
    ) -> list[Memory]:

        return [
            memory
            for memory in self.memories.values()
            if memory.memory_key == memory_key
        ]


class FakeRetriever:

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        return []


def test_find_memory_by_key():

    from assistant.memory import MemoryManager

    store = FakeMemoryStore()
    retriever = FakeRetriever()

    manager = MemoryManager(
        store=store,
        retriever=retriever,
    )

    manager.remember(
        content="I prefer Python.",
        memory_type="preference",
        memory_key="preferred_programming_language",
    )

    results = manager.find_by_key(
        "preferred_programming_language"
    )

    assert len(results) == 1

    assert results[0].content == (
        "I prefer Python."
    )


def test_update_memory_content():

    from assistant.memory import MemoryManager

    store = FakeMemoryStore()
    retriever = FakeRetriever()

    manager = MemoryManager(
        store=store,
        retriever=retriever,
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_type="preference",
        memory_key="preferred_programming_language",
    )

    original_id = memory.id

    updated = manager.update_memory(
        memory_id=memory.id,
        content="I now prefer Rust.",
    )

    assert updated.content == (
        "I now prefer Rust."
    )

    assert updated.id == original_id

    assert (
        updated.memory_key
        == "preferred_programming_language"
    )


def test_update_memory_importance():

    from assistant.memory import MemoryManager

    store = FakeMemoryStore()
    retriever = FakeRetriever()

    manager = MemoryManager(
        store=store,
        retriever=retriever,
    )

    memory = manager.remember(
        content="I prefer Python.",
        importance=0.5,
        memory_key="preferred_programming_language",
    )

    updated = manager.update_memory(
        memory_id=memory.id,
        importance=0.9,
    )

    assert updated.importance == 0.9


def test_update_missing_memory_fails():

    from assistant.memory import MemoryManager

    store = FakeMemoryStore()
    retriever = FakeRetriever()

    manager = MemoryManager(
        store=store,
        retriever=retriever,
    )

    with pytest.raises(ValueError):

        manager.update_memory(
            memory_id="does-not-exist",
            content="New content",
        )