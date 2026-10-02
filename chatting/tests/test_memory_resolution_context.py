from datetime import datetime

import pytest

from assistant.memory_candidate import MemoryCandidate
from assistant.memory_model import Memory
from assistant.memory_resolution_context import (
    MemoryResolutionContextBuilder,
)


def create_candidate(
    memory_id: str,
    content: str,
    similarity: float = 0.9,
    ranking_score: float = 0.8,
) -> MemoryCandidate:

    memory = Memory(
        id=memory_id,
        content=content,
        created_at=datetime.now(),
        memory_type="preference",
    )

    return MemoryCandidate(
        memory=memory,
        similarity=similarity,
        ranking_score=ranking_score,
    )


def test_builder_limits_candidates():

    candidates = [
        create_candidate(
            memory_id=f"memory-{index}",
            content=f"Memory {index}",
        )
        for index in range(10)
    ]

    builder = MemoryResolutionContextBuilder(
        max_candidates=5,
    )

    result = builder.build(candidates)

    assert len(result.candidates) == 5


def test_builder_keeps_best_candidates_first():

    candidates = [
        create_candidate(
            memory_id="memory-1",
            content="First memory",
        ),
        create_candidate(
            memory_id="memory-2",
            content="Second memory",
        ),
    ]

    builder = MemoryResolutionContextBuilder(
        max_candidates=1,
    )

    result = builder.build(candidates)

    assert len(result.candidates) == 1
    assert (
        result.candidates[0].memory.id
        == "memory-1"
    )


def test_builder_truncates_long_memory():

    long_content = "Python " * 500

    candidate = create_candidate(
        memory_id="memory-1",
        content=long_content,
    )

    builder = MemoryResolutionContextBuilder(
        max_content_characters=100,
    )

    result = builder.build([candidate])

    assert len(
        result.candidates[0].memory.content
    ) > 100

    assert "[Candidate context truncated.]" not in (
        result.text
    )

    assert "..." in result.text


def test_builder_limits_total_context():

    candidates = [
        create_candidate(
            memory_id=f"memory-{index}",
            content="Python " * 100,
        )
        for index in range(5)
    ]

    builder = MemoryResolutionContextBuilder(
        max_candidates=5,
        max_characters=500,
        max_content_characters=1000,
    )

    result = builder.build(candidates)

    assert len(result.text) > 500
    assert "[Candidate context truncated.]" in (
        result.text
    )


def test_empty_candidates():

    builder = MemoryResolutionContextBuilder()

    result = builder.build([])

    assert result.candidates == []
    assert result.text == ""


def test_invalid_max_candidates():

    with pytest.raises(ValueError):

        MemoryResolutionContextBuilder(
            max_candidates=0,
        )


def test_invalid_max_characters():

    with pytest.raises(ValueError):

        MemoryResolutionContextBuilder(
            max_characters=0,
        )


def test_invalid_max_content_characters():

    with pytest.raises(ValueError):

        MemoryResolutionContextBuilder(
            max_content_characters=0,
        )