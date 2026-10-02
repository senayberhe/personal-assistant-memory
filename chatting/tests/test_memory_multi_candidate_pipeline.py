from datetime import datetime
from unittest.mock import MagicMock

from assistant.memory.manager import (
    MemoryManager,
)
from assistant.memory.resolution.result import (
    MemoryResolutionResult,
)
from assistant.memory.resolution.types import (
    MemoryResolution,
)
from assistant.memory.retrieval.candidate import (
    MemoryCandidate,
)


def create_memory(
    memory_id: str,
    content: str,
    importance: float = 0.8,
):
    from assistant.memory.model import Memory

    return Memory(
        id=memory_id,
        content=content,
        created_at=datetime.now(),
        importance=importance,
    )


def test_multi_candidate_pipeline_updates_target_memory():

    store = MagicMock()

    target = create_memory(
        memory_id="memory-1",
        content="I prefer Python.",
    )

    unrelated = create_memory(
        memory_id="memory-2",
        content="I use VS Code.",
    )

    store.get_all.return_value = [
        target,
        unrelated,
    ]

    candidate_retriever = MagicMock()

    candidate_retriever.retrieve_candidates.return_value = [
        MemoryCandidate(
            memory=target,
            similarity=0.95,
            ranking_score=0.90,
        ),
        MemoryCandidate(
            memory=unrelated,
            similarity=0.60,
            ranking_score=0.50,
        ),
    ]

    candidate_ranker = MagicMock()

    candidate_ranker.rank.return_value = (
        candidate_retriever
        .retrieve_candidates.return_value
    )

    resolver = MagicMock()

    resolver.resolve.return_value = (
        MemoryResolutionResult(
            resolution=(
                MemoryResolution.CONTRADICT
            ),
            confidence=0.98,
            reason=(
                "The new preference conflicts "
                "with the existing preference."
            ),
            target_memory_id="memory-1",
        )
    )

    policy = MagicMock()

    from assistant.memory.policy import (
        MemoryPolicyDecision,
    )

    policy.decide.return_value = (
        MemoryPolicyDecision(
            resolution=(
                MemoryResolution.CONTRADICT
            ),
            action="update",
            requires_confirmation=False,
            allowed=True,
            reason="Update target.",
        )
    )

    manager = MemoryManager(
        store=store,
        retriever=MagicMock(),
        resolver=resolver,
        policy=policy,
        candidate_retriever=candidate_retriever,
        candidate_ranker=candidate_ranker,
    )

    result = manager.upsert(
        content="I don't prefer Python anymore.",
        candidate_limit=20,
        top_k=5,
    )

    assert result.id == "memory-1"

    resolver.resolve.assert_called_once()

    call = resolver.resolve.call_args

    assert call.kwargs[
        "new_content"
    ] == "I don't prefer Python anymore."

    assert len(
        call.kwargs["candidates"]
    ) == 2

    assert (
        call.kwargs["candidates"][0]
        .memory.id
        == "memory-1"
    )


def test_multi_candidate_pipeline_creates_new_memory():
    store = MagicMock()

    existing = create_memory(
        memory_id="memory-1",
        content="I prefer Python.",
    )

    store.get_all.return_value = [
        existing,
    ]

    candidate_retriever = MagicMock()

    candidate_retriever.retrieve_candidates.return_value = [
        MemoryCandidate(
            memory=existing,
            similarity=0.95,
            ranking_score=0.90,
        ),
    ]

    candidate_ranker = MagicMock()

    candidate_ranker.rank.return_value = (
        candidate_retriever
        .retrieve_candidates.return_value
    )

    resolver = MagicMock()

    resolver.resolve.return_value = (
        MemoryResolutionResult(
            resolution=(
                MemoryResolution.CREATE
            ),
            confidence=0.98,
            reason=(
                "No existing memory conflicts."
            ),
            target_memory_id=None,
        )
    )

    policy = MagicMock()

    from assistant.memory.policy import (
        MemoryPolicyDecision,
    )

    policy.decide.return_value = (
        MemoryPolicyDecision(
            resolution=(
                MemoryResolution.CREATE
            ),
            action="create",
            requires_confirmation=False,
            allowed=True,
            reason="Create new memory.",
        )
    )

    manager = MemoryManager(
        store=store,
        retriever=MagicMock(),
        resolver=resolver,
        policy=policy,
        candidate_retriever=candidate_retriever,
        candidate_ranker=candidate_ranker,
    )

    result = manager.upsert(
        content="I also like JavaScript.",
        candidate_limit=20,
        top_k=5,
    )

    assert result.id != "memory-1"

    resolver.resolve.assert_called_once()

    call = resolver.resolve.call_args

    assert call.kwargs[
        "new_content"
    ] == "I also like JavaScript."

    assert len(
        call.kwargs["candidates"]
    ) == 1

    assert (
        call.kwargs["candidates"][0]
        .memory.id
        == "memory-1"
    )

def test_key_match_is_first_candidate_even_if_search_misses_it():
    from assistant.memory.resolution.rules import MemoryResolver
    from assistant.memory.storage.in_memory import InMemoryStore
    from tests.fakes.memory_confirmation import FakeMemoryConfirmation

    store = InMemoryStore()

    other = create_memory("memory-2", "I use VS Code.")
    store.save(other)

    candidate_retriever = MagicMock()
    candidate_retriever.retrieve_candidates.return_value = [
        MemoryCandidate(memory=other, similarity=0.9, ranking_score=0.9),
    ]

    manager = MemoryManager(
        store=store,
        retriever=MagicMock(),
        resolver=MemoryResolver(),
        confirmation=FakeMemoryConfirmation(approved=True),
        candidate_retriever=candidate_retriever,
    )

    keyed = manager.remember("I prefer Python.", memory_key="lang")

    result = manager.upsert("I don't prefer Python.", memory_key="lang")

    # The rule-based resolver compared against the keyed
    # memory, not the unrelated top search result.
    assert result.id == keyed.id
    assert result.content == "I don't prefer Python."


def test_invalid_ai_answer_falls_back_to_rules():
    from assistant.memory.resolution.resilient import ResilientMemoryResolver
    from assistant.memory.resolution.rules import MemoryResolver

    ai_resolver = MagicMock()
    ai_resolver.resolve.side_effect = ValueError(
        "AI returned a target memory ID that was not present."
    )

    resolver = ResilientMemoryResolver(
        ai_resolver=ai_resolver,
        fallback_resolver=MemoryResolver(),
    )

    existing = create_memory("memory-1", "I prefer Python.")

    result = resolver.resolve(
        new_content="I prefer Python.",
        existing_memory=existing,
    )

    assert result.resolution == MemoryResolution.IGNORE
    assert result.target_memory_id == "memory-1"
