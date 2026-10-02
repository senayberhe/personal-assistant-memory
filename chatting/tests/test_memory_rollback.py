from assistant.memory.history.chroma import (
    ChromaMemoryHistoryStore,
)
from assistant.memory.manager import (
    MemoryManager,
)
from assistant.memory.storage.chroma import (
    ChromaMemoryStore,
)


class FakeRetriever:
    def retrieve(
        self,
        query,
        top_k=5,
        memory_type=None,
    ):
        return []


def create_manager(tmp_path):
    memory_store = ChromaMemoryStore(
        persist_directory=str(tmp_path),
        collection_name="memories",
    )

    history_store = (
        ChromaMemoryHistoryStore(
            persist_directory=str(tmp_path),
            collection_name="history",
        )
    )

    return MemoryManager(
        store=memory_store,
        retriever=FakeRetriever(),
        history_store=history_store,
    )


def test_restore_previous_version(
    tmp_path,
):
    manager = create_manager(tmp_path)

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

    restored = (
        manager.restore_memory_version(
            memory_id=memory.id,
            version=1,
        )
    )

    assert restored.version == 4

    assert restored.content == (
        "I prefer Python."
    )


def test_rollback_preserves_history(
    tmp_path,
):
    manager = create_manager(tmp_path)

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

    manager.restore_memory_version(
        memory_id=memory.id,
        version=1,
    )

    history = manager.get_history(
        memory.id
    )

    assert len(history) == 3

    assert history[0].version == 1
    assert history[0].content == (
        "I prefer Python."
    )

    assert history[1].version == 2
    assert history[1].content == (
        "I prefer TypeScript."
    )

    assert history[2].version == 3
    assert history[2].content == (
        "I prefer Rust."
    )


def test_rollback_creates_new_version(
    tmp_path,
):
    manager = create_manager(tmp_path)

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

    restored = (
        manager.restore_memory_version(
            memory_id=memory.id,
            version=1,
        )
    )

    assert restored.version == 3

    assert restored.content == (
        "I prefer Python."
    )


def test_rollback_unknown_version_fails(
    tmp_path,
):
    manager = create_manager(tmp_path)

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    try:
        manager.restore_memory_version(
            memory_id=memory.id,
            version=99,
        )
    except ValueError as error:
        assert "Version 99" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_rollback_unknown_memory_fails(
    tmp_path,
):
    manager = create_manager(tmp_path)

    try:
        manager.restore_memory_version(
            memory_id="does-not-exist",
            version=1,
        )
    except ValueError as error:
        assert "does-not-exist" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_rollback_requires_history_store(
    tmp_path,
):
    memory_store = ChromaMemoryStore(
        persist_directory=str(tmp_path),
        collection_name="memories",
    )

    manager = MemoryManager(
        store=memory_store,
        retriever=FakeRetriever(),
        history_store=None,
    )

    memory = manager.remember(
        content="I prefer Python.",
    )

    try:
        manager.restore_memory_version(
            memory_id=memory.id,
            version=1,
        )
    except RuntimeError as error:
        assert "history" in str(
            error
        ).lower()
    else:
        raise AssertionError(
            "Expected RuntimeError."
        )