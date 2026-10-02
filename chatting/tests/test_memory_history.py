from assistant.memory import (
    Memory,
    MemoryManager,
)
from assistant.memory.history.model import (
    MemoryVersion,
)
from assistant.memory.history.base import (
    MemoryHistoryStore,
)


class FakeMemoryStore:

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
            for memory
            in self.memories.values()
            if memory.memory_key
            == memory_key
        ]


class FakeRetriever:

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):

        return []


class FakeHistoryStore(
    MemoryHistoryStore
):

    def __init__(self):

        self.versions = []

    def save_version(
        self,
        version: MemoryVersion,
    ) -> None:

        self.versions.append(
            version
        )

    def get_history(
        self,
        memory_id: str,
    ) -> list[MemoryVersion]:

        return [
            version
            for version
            in self.versions
            if version.memory_id
            == memory_id
        ]


def create_manager():

    store = FakeMemoryStore()

    retriever = FakeRetriever()

    history_store = (
        FakeHistoryStore()
    )

    manager = MemoryManager(
        store=store,
        retriever=retriever,
        history_store=history_store,
    )

    return (
        manager,
        history_store,
    )


def test_new_memory_starts_at_version_one():

    manager, _ = create_manager()

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    assert memory.version == 1


def test_update_increments_version():

    manager, _ = create_manager()

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    updated = manager.update_memory(
        memory_id=memory.id,
        content="I prefer Rust.",
    )

    assert updated.version == 2


def test_update_preserves_memory_id():

    manager, _ = create_manager()

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    original_id = memory.id

    updated = manager.update_memory(
        memory_id=memory.id,
        content="I prefer Rust.",
    )

    assert updated.id == original_id


def test_previous_version_is_saved():

    manager, history_store = (
        create_manager()
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer Rust.",
    )

    history = (
        history_store.get_history(
            memory.id
        )
    )

    assert len(history) == 1

    assert history[0].version == 1

    assert history[0].content == (
        "I prefer Python."
    )


def test_multiple_updates_create_history():

    manager, history_store = (
        create_manager()
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer Rust.",
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer Go.",
    )

    history = (
        history_store.get_history(
            memory.id
        )
    )

    assert len(history) == 2

    assert history[0].version == 1

    assert history[0].content == (
        "I prefer Python."
    )

    assert history[1].version == 2

    assert history[1].content == (
        "I prefer Rust."
    )


def test_current_memory_contains_latest_version():

    manager, _ = create_manager()

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer Rust.",
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer Go.",
    )

    memories = (
        manager.store.get_all()
    )

    assert len(memories) == 1

    current = memories[0]

    assert current.version == 3

    assert current.content == (
        "I prefer Go."
    )

def test_rejected_update_records_no_history():
    import pytest

    manager, history_store = create_manager()

    memory = manager.remember(content="I prefer Python.")

    with pytest.raises(ValueError):
        manager.update_memory(memory_id=memory.id, content="   ")

    with pytest.raises(ValueError):
        manager.update_memory(memory_id=memory.id, importance=2.0)

    assert history_store.get_history(memory.id) == []
    assert memory.version == 1


def test_history_records_key_and_time():
    manager, history_store = create_manager()

    memory = manager.remember(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
    )

    manager.update_memory(memory_id=memory.id, content="I prefer Rust.")

    [version] = history_store.get_history(memory.id)

    assert version.memory_key == "preferred_programming_language"
    assert version.recorded_at >= version.created_at


def test_upsert_with_same_content_is_ignored():
    manager, history_store = create_manager()

    first = manager.upsert(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
    )

    second = manager.upsert(
        content="  i prefer PYTHON.  ",
        memory_key="preferred_programming_language",
    )

    assert second is first
    assert second.version == 1
    assert history_store.get_history(first.id) == []


def test_memory_module_reexports_single_memory_class():
    from assistant import memory
    from assistant.memory import manager, model

    assert memory.Memory is model.Memory
    assert memory.MemoryManager is manager.MemoryManager
