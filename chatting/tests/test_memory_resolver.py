from datetime import datetime

from assistant.memory.model import Memory
from assistant.memory.resolution.rules import (
    MemoryResolver,
)
from assistant.memory.resolution.types import (
    MemoryResolution,
)


def create_memory(
    content: str,
) -> Memory:
    return Memory(
        id="memory-1",
        content=content,
        created_at=datetime.now(),
        memory_key=(
            "preferred_programming_language"
        ),
    )


def test_no_existing_memory_creates():
    resolver = MemoryResolver()

    result = resolver.resolve(
        new_content="I prefer Python.",
        existing_memory=None,
    )

    assert result.resolution == (
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

    assert result.resolution == (
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

    assert result.resolution == (
        MemoryResolution.IGNORE
    )


def test_different_related_content_updates():
    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    result = resolver.resolve(
        new_content="I prefer Python programming.",
        existing_memory=existing,
    )

    assert result.resolution == (
        MemoryResolution.UPDATE
    )


def test_contradiction_is_detected():
    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=existing,
    )

    assert result.resolution == (
        MemoryResolution.CONTRADICT
    )


def test_unrelated_content_is_detected():
    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    result = resolver.resolve(
        new_content="My favorite color is blue.",
        existing_memory=existing,
    )

    assert result.resolution == (
        MemoryResolution.UNRELATED
    )


def test_empty_new_content_is_rejected():
    resolver = MemoryResolver()

    existing = create_memory(
        "I prefer Python."
    )

    try:
        resolver.resolve(
            new_content="",
            existing_memory=existing,
        )
    except ValueError as error:
        assert "empty" in str(
            error
        ).lower()
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_result_includes_confidence_and_reason():
    resolver = MemoryResolver()

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=create_memory("I prefer Python."),
    )

    assert 0.0 <= result.confidence <= 1.0
    assert result.reason
