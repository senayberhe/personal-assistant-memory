from datetime import datetime

import pytest

from assistant.memory_candidate import (
    MemoryCandidate,
)
from assistant.memory_evidence_builder import (
    MemoryEvidenceBuilder,
)
from assistant.memory_model import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_evidence import (
    ResolutionEvidence,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
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
    )

    return MemoryCandidate(
        memory=memory,
        similarity=similarity,
        ranking_score=ranking_score,
    )


def test_evidence_uses_target_candidate():

    candidate = create_candidate(
        memory_id="memory-1",
        content="I prefer Python.",
        similarity=0.95,
        ranking_score=0.88,
    )

    result = MemoryResolutionResult(
        resolution=MemoryResolution.CONTRADICT,
        confidence=0.97,
        reason="The preferences conflict.",
        target_memory_id="memory-1",
    )

    evidence = MemoryEvidenceBuilder.build(
        result=result,
        candidates=[candidate],
    )

    assert evidence.target_memory_id == "memory-1"
    assert evidence.similarity == 0.95
    assert evidence.ranking_score == 0.88
    assert evidence.confidence == 0.97


def test_evidence_without_target():

    result = MemoryResolutionResult(
        resolution=MemoryResolution.CREATE,
        confidence=1.0,
        reason="No related memory exists.",
    )

    evidence = MemoryEvidenceBuilder.build(
        result=result,
        candidates=[],
    )

    assert evidence.target_memory_id is None
    assert evidence.similarity is None
    assert evidence.ranking_score is None


def test_unknown_target_has_no_candidate_scores():

    candidate = create_candidate(
        memory_id="memory-1",
        content="I prefer Python.",
    )

    result = MemoryResolutionResult(
        resolution=MemoryResolution.UPDATE,
        confidence=0.8,
        reason="Related memory.",
        target_memory_id="unknown-memory",
    )

    evidence = MemoryEvidenceBuilder.build(
        result=result,
        candidates=[candidate],
    )

    assert (
        evidence.target_memory_id
        == "unknown-memory"
    )

    assert evidence.similarity is None
    assert evidence.ranking_score is None


def test_invalid_confidence():

    with pytest.raises(ValueError):

        ResolutionEvidence(
            target_memory_id=None,
            similarity=None,
            ranking_score=None,
            confidence=1.5,
            reason="Invalid confidence.",
        )


def test_invalid_similarity():

    with pytest.raises(ValueError):

        ResolutionEvidence(
            target_memory_id="memory-1",
            similarity=1.5,
            ranking_score=0.8,
            confidence=0.9,
            reason="Invalid similarity.",
        )


def test_empty_reason_rejected():

    with pytest.raises(ValueError):

        ResolutionEvidence(
            target_memory_id=None,
            similarity=None,
            ranking_score=None,
            confidence=0.9,
            reason="",
        )