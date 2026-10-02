
from assistant.chroma_memory_history_store import (
    ChromaMemoryHistoryStore,
)
from assistant.chroma_memory_store import (
    ChromaMemoryStore,
)
from assistant.memory_manager import (
    MemoryManager,
)


class FakeRetriever:

    def retrieve(
        self,
        query,
        top_k=5,
        memory_type=None,
    ):
        return []


def test_update_saves_previous_version(
    tmp_path,
):
    memory_store = ChromaMemoryStore(
        persist_directory=str(tmp_path),
        collection_name="memories",
    )

    history_store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="history",
    )

    manager = MemoryManager(
        store=memory_store,
        retriever=FakeRetriever(),
        history_store=history_store,
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_type="preference",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    assert memory.version == 1

    updated = manager.update_memory(
        memory_id=memory.id,
        content="I now prefer Rust.",
    )

    assert updated.version == 2

    history = manager.get_history(
        memory.id
    )

    assert len(history) == 1

    assert history[0].version == 1

    assert history[0].content == (
        "I prefer Python."
    )


def test_multiple_updates_create_history(
    tmp_path,
):
    memory_store = ChromaMemoryStore(
        persist_directory=str(tmp_path),
        collection_name="multi_memories",
    )

    history_store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="multi_history",
    )

    manager = MemoryManager(
        store=memory_store,
        retriever=FakeRetriever(),
        history_store=history_store,
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer TypeScript.",
    )

    manager.update_memory(
        memory_id=memory.id,
        content="I prefer Rust.",
    )

    history = manager.get_history(
        memory.id
    )

    assert len(history) == 2

    assert history[0].version == 1
    assert history[0].content == (
        "I prefer Python."
    )

    assert history[1].version == 2
    assert history[1].content == (
        "I prefer TypeScript."
    )

    current_memories = (
        memory_store.get_all()
    )

    assert len(current_memories) == 1

    current = current_memories[0]

    assert current.version == 3

    assert current.content == (
        "I prefer Rust."
    )