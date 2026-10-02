import pytest

from datetime import datetime, timedelta

from assistant.memory.retrieval.candidate import (
    MemoryCandidate,
)
from assistant.memory.retrieval.candidate_ranker import (
    MemoryCandidateRanker,
)
from assistant.memory.model import Memory


def create_memory(
    memory_id: str,
    content: str,
    importance: float,
    age_days: int,
) -> Memory:

    return Memory(
        id=memory_id,
        content=content,
        created_at=(
            datetime.now()
            - timedelta(days=age_days)
        ),
        importance=importance,
    )


def test_ranker_returns_same_number_of_candidates():

    candidates = [
        MemoryCandidate(
            memory=create_memory(
                memory_id="memory-1",
                content="I prefer Python.",
                importance=0.9,
                age_days=1,
            ),
            similarity=0.90,
            ranking_score=0.90,
        ),
        MemoryCandidate(
            memory=create_memory(
                memory_id="memory-2",
                content="I use VS Code.",
                importance=0.5,
                age_days=10,
            ),
            similarity=0.80,
            ranking_score=0.80,
        ),
    ]

    ranker = MemoryCandidateRanker()

    results = ranker.rank(candidates)

    assert len(results) == 2


def test_ranker_orders_by_final_score():

    candidates = [
        MemoryCandidate(
            memory=create_memory(
                memory_id="low",
                content="Low relevance",
                importance=0.1,
                age_days=100,
            ),
            similarity=0.40,
            ranking_score=0.40,
        ),
        MemoryCandidate(
            memory=create_memory(
                memory_id="high",
                content="High relevance",
                importance=0.9,
                age_days=1,
            ),
            similarity=0.95,
            ranking_score=0.95,
        ),
    ]

    ranker = MemoryCandidateRanker()

    results = ranker.rank(candidates)

    assert results[0].memory.id == "high"
    assert results[1].memory.id == "low"


def test_ranker_calculates_new_ranking_score():

    memory = create_memory(
        memory_id="memory-1",
        content="I prefer Python.",
        importance=0.8,
        age_days=1,
    )

    candidate = MemoryCandidate(
        memory=memory,
        similarity=0.9,
        ranking_score=0.0,
    )

    ranker = MemoryCandidateRanker()

    result = ranker.rank([candidate])

    assert result[0].ranking_score > 0.0


def test_ranker_does_not_mutate_original_candidate():

    memory = create_memory(
        memory_id="memory-1",
        content="I prefer Python.",
        importance=0.8,
        age_days=1,
    )

    candidate = MemoryCandidate(
        memory=memory,
        similarity=0.9,
        ranking_score=0.9,
    )

    ranker = MemoryCandidateRanker()

    result = ranker.rank([candidate])

    assert candidate.ranking_score == 0.9
    assert result[0].ranking_score != 0.9


def test_empty_candidate_list():
    ranker = MemoryCandidateRanker()
    result = ranker.rank([])
    assert result == []

def test_invalid_decay_days():
    with pytest.raises(ValueError):
        MemoryCandidateRanker(
            recency_decay_days=0
        )


def test_ranker_limits_results_to_top_k():
    candidates = []

    for index in range(10):
        memory = create_memory(
            memory_id=f"memory-{index}",
            content = f"Memory {index}",
            importance=0.5,
            age_days = index,
        )
        candidates.append(
            MemoryCandidate(
                memory=memory,
                similarity=1.0 - (
                    index * 0.05
                ),
                ranking_score=0.0,
            )
        )
    ranker = MemoryCandidateRanker()

    results = ranker.rank(
        candidates,
        top_k=5
    )

    assert len(results) == 5


def test_ranker_returns_all_when_top_k_is_none():
    candidates = []

    for index in range(4):
        memory = create_memory(
            memory_id=f"memory-{index}",
            content=f"Memory {index}",
            importance=0.5,
            age_days = index,
        )
        candidates.append(
            MemoryCandidate(
                memory=memory,
                similarity=1.0 - (
                    index * 0.05
                ),
                ranking_score=0.0,
            )
        )

    ranker = MemoryCandidateRanker()

    results = ranker.rank(
        candidates,
        top_k=None
    )

    assert len(results) == 4


def test_ranker_with_top_k_larger_then_candidates():
    candidates = [
        MemoryCandidate(
            memory=create_memory(
                memory_id="memory-1",
                content="Memory 1",
                importance=0.5,
                age_days=1,
            ),
            similarity=0.9,
            ranking_score=0.0,
        )
    ]

    ranker = MemoryCandidateRanker()

    results = ranker.rank(
        candidates,
        top_k=5
    )

    assert len(results) == 1



def test_ranker_with_zero_top_k_returns_empty():
    candidates = [
        MemoryCandidate(
            memory=create_memory(
                memory_id="memory-1",
                content="Python",
                importance=0.8,
                age_days=1,
            ),
            similarity=0.9,
            ranking_score=0.0,
        )
    ]

    ranker = MemoryCandidateRanker()

    results = ranker.rank(
        candidates,
        top_k=0,
    )

    assert results == []