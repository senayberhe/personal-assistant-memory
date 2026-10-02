from datetime import datetime

from assistant.chroma_memory_history_store import (
    ChromaMemoryHistoryStore,
)
from assistant.memory_history import MemoryVersion


def create_version(
    memory_id: str,
    version: int,
    content: str,
) -> MemoryVersion:

    now = datetime.now()

    return MemoryVersion(
        memory_id=memory_id,
        version=version,
        content=content,
        created_at=now,
        recorded_at=now,
        memory_key=(
            "preferred_programming_language"
        ),
    )


def test_save_and_get_history(
    tmp_path,
):
    store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="test_history",
    )

    version = create_version(
        memory_id="memory-1",
        version=1,
        content="I prefer Python.",
    )

    store.save_version(version)

    history = store.get_history(
        "memory-1"
    )

    assert len(history) == 1

    assert history[0].memory_id == (
        "memory-1"
    )

    assert history[0].version == 1

    assert history[0].content == (
        "I prefer Python."
    )


def test_multiple_versions_are_returned_in_order(
    tmp_path,
):
    store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="test_history_order",
    )

    version_1 = create_version(
        memory_id="memory-1",
        version=1,
        content="I prefer Python.",
    )

    version_2 = create_version(
        memory_id="memory-1",
        version=2,
        content="I prefer TypeScript.",
    )

    version_3 = create_version(
        memory_id="memory-1",
        version=3,
        content="I prefer Rust.",
    )

    # Save deliberately out of order.
    store.save_version(version_3)
    store.save_version(version_1)
    store.save_version(version_2)

    history = store.get_history(
        "memory-1"
    )

    assert len(history) == 3

    assert [
        item.version
        for item in history
    ] == [1, 2, 3]

    assert [
        item.content
        for item in history
    ] == [
        "I prefer Python.",
        "I prefer TypeScript.",
        "I prefer Rust.",
    ]


def test_history_persists_between_store_instances(
    tmp_path,
):
    version = create_version(
        memory_id="memory-1",
        version=1,
        content="I am learning Python.",
    )

    first_store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="persistent_history",
    )

    first_store.save_version(
        version
    )

    second_store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="persistent_history",
    )

    history = second_store.get_history(
        "memory-1"
    )

    assert len(history) == 1

    assert history[0].content == (
        "I am learning Python."
    )


def test_history_for_unknown_memory_is_empty(
    tmp_path,
):
    store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="empty_history",
    )

    history = store.get_history(
        "does-not-exist"
    )

    assert history == []


def test_different_memories_have_separate_history(
    tmp_path,
):
    store = ChromaMemoryHistoryStore(
        persist_directory=str(tmp_path),
        collection_name="separate_history",
    )

    store.save_version(
        create_version(
            memory_id="memory-1",
            version=1,
            content="I prefer Python.",
        )
    )

    store.save_version(
        create_version(
            memory_id="memory-2",
            version=1,
            content="I prefer Rust.",
        )
    )

    history_one = store.get_history(
        "memory-1"
    )

    history_two = store.get_history(
        "memory-2"
    )

    assert len(history_one) == 1
    assert len(history_two) == 1

    assert history_one[0].content == (
        "I prefer Python."
    )

    assert history_two[0].content == (
        "I prefer Rust."
    )