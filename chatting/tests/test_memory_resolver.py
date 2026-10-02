from datetime import datetime

from assistant.memory import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolver import (
    MemoryResolver,
)


def create_memory(
    content: str,
) -> Memory:

    return Memory(
        id="memory-1",
        content=content,
        created_at=datetime.now(),
        memory_key="preferred_programming_language",
    )


def test_no_existing_memory_creates():

    resolver = MemoryResolver()

    result = resolver.resolve(
        new_content="I prefer Python.",
        existing_memory=None,
    )

    assert result == (
        MemoryResolution.CREATE
    )


def test_same_content_is_ignored():

    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    result = resolver.resolve(
        new_content="I prefer Python.",
        existing_memory=existing,
    )

    assert result == (
        MemoryResolution.IGNORE
    )


def test_same_content_with_different_case_is_ignored():

    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    result = resolver.resolve(
        new_content="i PREFER python.",
        existing_memory=existing,
    )

    assert result == (
        MemoryResolution.IGNORE
    )


def test_different_content_updates():

    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    result = resolver.resolve(
        new_content="I now prefer Rust.",
        existing_memory=existing,
    )

    assert result == (
        MemoryResolution.UPDATE
    )