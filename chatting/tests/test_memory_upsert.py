import pytest

from assistant.memory import Memory, MemoryManager
from assistant.memory.storage.base import MemoryStore
from tests.fakes.memory_confirmation import FakeMemoryConfirmation


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


def create_manager() -> MemoryManager:

    store = FakeMemoryStore()

    retriever = FakeRetriever()

    # Changing a preference is an uncertain update under
    # MemoryPolicy, so approve confirmations automatically.
    return MemoryManager(
        store=store,
        retriever=retriever,
        confirmation=FakeMemoryConfirmation(approved=True),
    )


def test_upsert_creates_new_memory():

    manager = create_manager()

    memory = manager.upsert(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
        memory_type="preference",
        importance=0.9,
    )

    assert memory.content == (
        "I prefer Python."
    )

    assert (
        memory.memory_key
        == "preferred_programming_language"
    )

    assert memory.importance == 0.9


def test_upsert_updates_existing_memory():

    manager = create_manager()

    first = manager.upsert(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
        memory_type="preference",
        importance=0.9,
    )

    original_id = first.id

    second = manager.upsert(
        content="I now prefer Rust.",
        memory_key="preferred_programming_language",
        memory_type="preference",
        importance=0.95,
    )

    assert second.id == original_id

    assert second.content == (
        "I now prefer Rust."
    )

    assert second.importance == 0.95


def test_upsert_does_not_create_duplicate():

    manager = create_manager()

    manager.upsert(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
    )

    manager.upsert(
        content="I now prefer Rust.",
        memory_key="preferred_programming_language",
    )

    memories = manager.store.get_all()

    assert len(memories) == 1

    assert memories[0].content == (
        "I now prefer Rust."
    )


def test_different_keys_create_different_memories():

    manager = create_manager()

    manager.upsert(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
    )

    manager.upsert(
        content="I like coffee.",
        memory_key="favorite_drink",
    )

    memories = manager.store.get_all()

    assert len(memories) == 2


def test_empty_memory_key_fails():

    manager = create_manager()

    with pytest.raises(ValueError):

        manager.upsert(
            content="I prefer Python.",
            memory_key="",
        )


def test_whitespace_memory_key_fails():

    manager = create_manager()

    with pytest.raises(ValueError):

        manager.upsert(
            content="I prefer Python.",
            memory_key="   ",
        )