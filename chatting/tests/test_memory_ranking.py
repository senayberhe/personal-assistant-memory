from datetime import datetime, timedelta

from assistant.memory import Memory
from assistant.memory.ranking import (
    calculate_final_score,
    calculate_recency,
    rank_memories,
)
from assistant.memory.retrieval.base import RetrievedMemory


def test_new_memory_has_higher_recency():
    now = datetime.now()

    recent = calculate_recency(
        now,
        now=now,
    )

    old = calculate_recency(
        now - timedelta(days=90),
        now=now,
    )

    assert recent > old


def test_final_score():
    score = calculate_final_score(
        similarity=1.0,
        importance=1.0,
        recency=1.0,
    )

    assert score == 1.0


def test_final_score_uses_weighted_values():
    score = calculate_final_score(
        similarity=0.8,
        importance=0.6,
        recency=0.4,
    )

    expected = (
        0.60 * 0.8
        + 0.25 * 0.6
        + 0.15 * 0.4
    )

    assert abs(score - expected) < 0.000001


def test_rank_memories():
    now = datetime.now()

    memory_a = Memory(
        id="a",
        content="Learning Python",
        created_at=now,
        memory_type="learning",
        importance=0.9,
    )

    memory_b = Memory(
        id="b",
        content="Had coffee",
        created_at=now,
        memory_type="general",
        importance=0.1,
    )

    results = [
        RetrievedMemory(
            memory=memory_a,
            score=0.8,
        ),
        RetrievedMemory(
            memory=memory_b,
            score=0.7,
        ),
    ]

    ranked = rank_memories(
        results,
        now=now,
    )

    assert ranked[0].memory.id == "a"
    assert ranked[1].memory.id == "b"


def test_ranked_memory_contains_score_components():
    now = datetime.now()

    memory = Memory(
        id="python",
        content="I am learning Python.",
        created_at=now,
        memory_type="learning",
        importance=0.9,
    )

    result = RetrievedMemory(
        memory=memory,
        score=0.8,
    )

    ranked = rank_memories(
        [result],
        now=now,
    )

    ranked_memory = ranked[0]

    assert ranked_memory.memory.id == "python"
    assert ranked_memory.similarity == 0.8
    assert ranked_memory.importance == 0.9
    assert ranked_memory.recency == 1.0
    assert ranked_memory.final_score > 0


def test_more_important_memory_can_rank_higher():
    now = datetime.now()

    important_memory = Memory(
        id="important",
        content="I am learning Python.",
        created_at=now,
        memory_type="learning",
        importance=1.0,
    )

    less_important_memory = Memory(
        id="less-important",
        content="I once mentioned Python.",
        created_at=now,
        memory_type="general",
        importance=0.1,
    )

    results = [
        RetrievedMemory(
            memory=less_important_memory,
            score=0.8,
        ),
        RetrievedMemory(
            memory=important_memory,
            score=0.8,
        ),
    ]

    ranked = rank_memories(
        results,
        now=now,
    )

    assert ranked[0].memory.id == "important"


def test_recent_memory_has_higher_recency_than_old_memory():
    now = datetime.now()

    recent_memory = Memory(
        id="recent",
        content="Recent memory",
        created_at=now - timedelta(days=1),
        importance=0.5,
    )

    old_memory = Memory(
        id="old",
        content="Old memory",
        created_at=now - timedelta(days=365),
        importance=0.5,
    )

    results = [
        RetrievedMemory(
            memory=old_memory,
            score=0.8,
        ),
        RetrievedMemory(
            memory=recent_memory,
            score=0.8,
        ),
    ]

    ranked = rank_memories(
        results,
        now=now,
    )

    assert ranked[0].memory.id == "recent"


def test_empty_results_return_empty_list():
    ranked = rank_memories([])

    assert ranked == []

def test_memory_manager_recall_ranked_uses_scores():
    from assistant.memory.embeddings import SimpleEmbeddingService
    from assistant.memory.retrieval.in_memory import InMemoryRetriever
    from assistant.memory.storage.in_memory import InMemoryStore
    from assistant.memory import MemoryManager

    store = InMemoryStore()

    manager = MemoryManager(
        store=store,
        retriever=InMemoryRetriever(
            memory_store=store,
            embedding_service=SimpleEmbeddingService(),
        ),
    )

    manager.remember("User likes Python", importance=0.9)
    manager.remember("User drinks tea", importance=0.1)
    manager.remember("User owns a cat", importance=0.5)

    ranked = manager.recall_ranked("User likes Python", top_k=2)

    assert len(ranked) == 2
    assert ranked[0].memory.content == "User likes Python"
    assert ranked[0].similarity > 0.99
    assert ranked[0].final_score >= ranked[1].final_score
