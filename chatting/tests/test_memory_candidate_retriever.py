from datetime import datetime
from unittest.mock import MagicMock

from assistant.memory.model import Memory
from assistant.memory.retrieval.base import RetrievedMemory
from assistant.memory.retrieval.candidate import (
    MemoryCandidate,
)
from assistant.memory.retrieval.scored_candidate_retriever import (
    ScoredCandidateRetriever,
)


def test_retrieve_candidates():

    memory = Memory(
        id="memory-1",
        content="I prefer Python.",
        created_at=datetime.now(),
    )

    retriever = MagicMock()

    retriever.retrieve_scored.return_value = [
        RetrievedMemory(
            memory=memory,
            score=0.91,
        )
    ]

    candidate_retriever = (
        ScoredCandidateRetriever(
            retriever=retriever
        )
    )

    candidates = (
        candidate_retriever.retrieve_candidates(
            query="What programming language do I prefer?",
            candidate_limit=10,
        )
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    assert isinstance(
        candidate,
        MemoryCandidate,
    )

    assert candidate.memory.id == "memory-1"

    assert candidate.similarity == 0.91

    assert candidate.ranking_score == 0.91


def test_empty_query_returns_empty_list():

    retriever = MagicMock()

    candidate_retriever = (
        ScoredCandidateRetriever(
            retriever=retriever
        )
    )

    result = (
        candidate_retriever.retrieve_candidates(
            query="",
            candidate_limit=10,
        )
    )

    assert result == []

    retriever.retrieve_scored.assert_not_called()


def test_invalid_candidate_limit_returns_empty_list():

    retriever = MagicMock()

    candidate_retriever = (
        ScoredCandidateRetriever(
            retriever=retriever
        )
    )

    result = (
        candidate_retriever.retrieve_candidates(
            query="Python",
            candidate_limit=0,
        )
    )

    assert result == []

    retriever.retrieve_scored.assert_not_called()