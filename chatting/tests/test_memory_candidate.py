from datetime import datetime

from assistant.memory_candidate import (
    MemoryCandidate,
)
from assistant.memory_model import Memory


def test_memory_candidate_stores_memory_and_scores():

    memory = Memory(
        id="memory-1",
        content="I prefer Python.",
        created_at=datetime.now(),
    )

    candidate = MemoryCandidate(
        memory=memory,
        similarity=0.91,
        ranking_score=0.87,
    )

    assert candidate.memory is memory
    assert candidate.similarity == 0.91
    assert candidate.ranking_score == 0.87