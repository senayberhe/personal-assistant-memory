"""
MemoryManager: the single entry point for long-term memory.

It owns the workflow (validate -> resolve -> decide -> confirm ->
store -> publish an event) and delegates each step to a focused
component, so each piece can be swapped or tested on its own.
"""

from datetime import datetime, timedelta
from uuid import uuid4

from assistant.memory.audit.base import MemoryAuditStore
from assistant.memory.confirmation import MemoryConfirmation
from assistant.memory.events.audit_listener import MemoryAuditListener
from assistant.memory.events.event import MemoryEvent
from assistant.memory.events.publisher import MemoryEventPublisher
from assistant.memory.guard import MemoryContentGuard
from assistant.memory.history.model import MemoryVersion
from assistant.memory.lifecycle import MemoryLifecycle
from assistant.memory.model import Memory, validate_importance
from assistant.memory.policy import MemoryPolicy
from assistant.memory.ranking import rank_memories
from assistant.memory.resolution.protocol import MemoryResolverProtocol
from assistant.memory.resolution.result import MemoryResolutionResult
from assistant.memory.resolution.rules import MemoryResolver
from assistant.memory.retrieval.candidate import MemoryCandidate
from assistant.memory.retrieval.candidate_ranker import MemoryCandidateRanker
from assistant.memory.retrieval.candidate_retriever import (
    MemoryCandidateRetriever,
)


class MemoryManager:
    """
    Coordinates memory creation, retrieval, resolution, updates,
    history, rollback, and deletion.

    Collaborators (all optional except store and retriever):

    - store / retriever: persistence and semantic search
    - resolver / policy / confirmation: decide what to do when a
      new memory relates to existing ones
    - candidate_retriever / candidate_ranker: find related memories
    - history_store: previous versions, for rollback
    - content_guard: rejects empty, oversized, or sensitive content
    - event_publisher: notifies listeners (logging, metrics, audit)
    """

    def __init__(
        self,
        store,
        retriever,
        resolver: MemoryResolverProtocol | None = None,
        history_store=None,
        policy: MemoryPolicy | None = None,
        confirmation: MemoryConfirmation | None = None,
        candidate_retriever: MemoryCandidateRetriever | None = None,
        candidate_ranker: MemoryCandidateRanker | None = None,
        audit_store: MemoryAuditStore | None = None,
        content_guard: MemoryContentGuard | None = None,
        event_publisher: MemoryEventPublisher | None = None,
    ):
        self.store = store
        self.retriever = retriever
        self.resolver = resolver or MemoryResolver()
        self.history_store = history_store
        self.policy = policy or MemoryPolicy()
        self.confirmation = confirmation
        self.candidate_retriever = candidate_retriever
        self.candidate_ranker = candidate_ranker or MemoryCandidateRanker()
        self.content_guard = content_guard or MemoryContentGuard()
        self.event_publisher = event_publisher or MemoryEventPublisher()

        # Convenience: passing an audit store records every
        # memory event as an audit record.
        self.audit_store = audit_store

        if audit_store is not None:
            self.event_publisher.subscribe(
                MemoryAuditListener(audit_store)
            )

    # --------------------------------------------------
    # Create
    # --------------------------------------------------

    def remember(
        self,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
        source: str = "conversation",
        metadata: dict | None = None,
        ttl_days: float | None = None,
        memory_key: str | None = None,
    ) -> Memory:
        """Create and store a new memory (always version 1)."""

        try:
            memory = self._create(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                metadata=metadata,
                ttl_days=ttl_days,
                memory_key=memory_key,
            )

        except Exception as error:
            self._publish_failure("memory_created", "create", content, error)
            raise

        self._publish(
            event_type="memory_created",
            action="create",
            content=memory.content,
            memory_id=memory.id,
            resulting_version=memory.version,
        )

        return memory

    def _create(
        self,
        content: str,
        memory_type: str,
        importance: float,
        source: str,
        metadata: dict | None,
        ttl_days: float | None,
        memory_key: str | None,
    ) -> Memory:

        content = self.content_guard.check(content)
        importance = validate_importance(importance)

        if memory_key is not None:
            memory_key = memory_key.strip() or None

        created_at = datetime.now()
        expires_at = None

        if ttl_days is not None:
            if ttl_days <= 0:
                raise ValueError("ttl_days must be greater than zero.")

            expires_at = created_at + timedelta(days=ttl_days)

        memory = Memory(
            id=uuid4().hex,
            content=content,
            created_at=created_at,
            memory_type=memory_type,
            importance=importance,
            source=source,
            metadata=metadata or {},
            expires_at=expires_at,
            memory_key=memory_key,
            version=1,
        )

        self.store.save(memory)

        return memory

    # --------------------------------------------------
    # Read
    # --------------------------------------------------

    def find_by_key(
        self,
        memory_key: str,
    ) -> list[Memory]:

        if not memory_key.strip():
            return []

        return self.store.find_by_key(memory_key)

    def get_all(self) -> list[Memory]:
        """All non-expired memories, newest first."""

        memories = MemoryLifecycle.filter_active(self.store.get_all())

        return sorted(
            memories,
            key=lambda memory: memory.created_at,
            reverse=True,
        )

    def recall(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[Memory]:
        """
        Retrieve relevant memories that have not expired.

        retriever.retrieve() already returns Memory objects
        (not scored results).
        """

        memories = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            memory_type=memory_type,
        )

        return MemoryLifecycle.filter_active(memories)

    def recall_scored(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        """
        Retrieve non-expired memories together with their
        similarity scores (RetrievedMemory objects).
        """

        results = self.retriever.retrieve_scored(
            query,
            top_k=top_k,
            memory_type=memory_type,
        )

        return [
            result
            for result in results
            if not MemoryLifecycle.is_expired(result.memory)
        ]

    def recall_ranked(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        """
        Retrieve and rank memories by similarity, importance,
        and recency.

        Extra candidates are fetched by similarity so that
        importance and recency can reorder them.
        """

        results = self.recall_scored(
            query,
            top_k=top_k * 3,
            memory_type=memory_type,
        )

        return rank_memories(results)[:top_k]

    def retrieve_candidates(
        self,
        query: str,
        candidate_limit: int = 20,
        top_k: int = 5,
    ) -> list[MemoryCandidate]:
        """
        Find memories related to `query`.

        1. Retrieve up to candidate_limit memories by similarity.
        2. Rerank them by similarity, importance, and recency.
        3. Return the top_k.
        """

        if (
            self.candidate_retriever is None
            or not query.strip()
            or candidate_limit <= 0
            or top_k <= 0
        ):
            return []

        candidates = self.candidate_retriever.retrieve_candidates(
            query=query,
            candidate_limit=candidate_limit,
        )

        return self.candidate_ranker.rank(candidates, top_k=top_k)

    # --------------------------------------------------
    # Update
    # --------------------------------------------------

    def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        importance: float | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        """
        Update an existing memory and bump its version.

        The previous version is saved to the history store first.
        Raises ValueError if the memory does not exist.
        """

        try:
            previous_version, memory = self._update(
                memory_id=memory_id,
                content=content,
                importance=importance,
                metadata=metadata,
            )

        except Exception as error:
            self._publish_failure(
                "memory_updated",
                "update",
                content or "",
                error,
                memory_id=memory_id,
            )
            raise

        self._publish(
            event_type="memory_updated",
            action="update",
            content=memory.content,
            memory_id=memory.id,
            previous_version=previous_version,
            resulting_version=memory.version,
        )

        return memory

    def _update(
        self,
        memory_id: str,
        content: str | None,
        importance: float | None,
        metadata: dict | None,
    ) -> tuple[int, Memory]:
        """Apply an update. Returns (previous_version, memory)."""

        memory = self._find_memory(memory_id)

        if memory is None:
            raise ValueError(f"Memory '{memory_id}' was not found.")

        # Validate first, so a rejected update leaves no
        # history entry behind.
        if content is not None:
            content = self.content_guard.check(content)

        if importance is not None:
            importance = validate_importance(importance)

        previous_version = memory.version

        if self.history_store is not None:
            self.history_store.save_version(
                MemoryVersion(
                    memory_id=memory.id,
                    version=memory.version,
                    content=memory.content,
                    created_at=memory.created_at,
                    recorded_at=datetime.now(),
                    memory_key=memory.memory_key,
                )
            )

        if content is not None:
            memory.content = content

        if importance is not None:
            memory.importance = importance

        if metadata is not None:
            memory.metadata = metadata

        memory.version += 1

        self.store.save(memory)

        return previous_version, memory

    def upsert(
        self,
        content: str,
        memory_key: str | None = None,
        memory_type: str = "general",
        importance: float = 0.5,
        source: str = "conversation",
        metadata: dict | None = None,
        ttl_days: float | None = None,
        candidate_limit: int = 20,
        top_k: int = 5,
    ) -> Memory:
        """
        Create, update, or ignore a memory.

        1. Find related memories (same key first, then semantic
           candidates).
        2. The resolver decides how the new content relates to them.
        3. The policy decides what to do; risky updates are confirmed.
        """

        try:
            # Check before anything else, so sensitive content is
            # never sent to the (possibly AI-based) resolver.
            content = self.content_guard.check(content)

            # memory_key is optional, but an explicitly blank key
            # is almost certainly a mistake.
            if memory_key is not None and not memory_key.strip():
                raise ValueError("memory_key cannot be empty.")

            return self._upsert(
                content=content,
                memory_key=memory_key,
                memory_type=memory_type,
                importance=importance,
                source=source,
                metadata=metadata,
                ttl_days=ttl_days,
                candidate_limit=candidate_limit,
                top_k=top_k,
            )

        except Exception as error:
            self._publish_failure("memory_upserted", "upsert", content, error)
            raise

    def _upsert(
        self,
        content: str,
        memory_key: str | None,
        memory_type: str,
        importance: float,
        source: str,
        metadata: dict | None,
        ttl_days: float | None,
        candidate_limit: int,
        top_k: int,
    ) -> Memory:

        keyed_memory = None

        if memory_key:
            matches = self.find_by_key(memory_key)

            if matches:
                keyed_memory = matches[0]

        candidates = self.retrieve_candidates(
            query=content,
            candidate_limit=candidate_limit,
            top_k=top_k,
        )

        # A memory with the same key is the strongest candidate even
        # if semantic search ranked it low or missed it.
        if keyed_memory is not None:
            candidates = [
                MemoryCandidate(
                    memory=keyed_memory,
                    similarity=1.0,
                    ranking_score=1.0,
                ),
                *(
                    candidate
                    for candidate in candidates
                    if candidate.memory.id != keyed_memory.id
                ),
            ]

        result = self.resolver.resolve(
            new_content=content,
            existing_memory=keyed_memory,
            candidates=candidates,
        )

        decision = self.policy.decide(
            resolution=result.resolution,
            confidence=result.confidence,
        )

        if not decision.allowed:
            raise PermissionError(decision.reason)

        def create() -> Memory:
            memory = self._create(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                metadata=metadata,
                ttl_days=ttl_days,
                memory_key=memory_key,
            )

            self._publish_decision(
                "create", content, result, memory, resulting=memory.version
            )

            return memory

        if decision.action == "create":
            return create()

        target = self._resolve_target(result, keyed_memory)

        if decision.action == "ignore":
            if target is None:
                # Nothing to match against: treat it as new.
                return create()

            self._publish_decision("ignore", content, result, target)

            return target

        if decision.action == "update":
            if target is None:
                raise ValueError(
                    "Memory update requires a target memory "
                    f"(target_memory_id={result.target_memory_id!r})."
                )

            if decision.requires_confirmation and not self._confirm_update(
                target, content, result
            ):
                self._publish_decision(
                    "update_declined", content, result, target
                )

                return target

            previous_version, memory = self._update(
                memory_id=target.id,
                content=content,
                importance=importance,
                metadata=metadata,
            )

            self._publish_decision(
                "update",
                content,
                result,
                memory,
                previous=previous_version,
                resulting=memory.version,
            )

            return memory

        raise RuntimeError(
            f"Unsupported memory policy action: {decision.action}"
        )

    def _resolve_target(
        self,
        result: MemoryResolutionResult,
        keyed_memory: Memory | None,
    ) -> Memory | None:
        """The memory the resolver pointed at, if it exists."""

        if result.target_memory_id:
            target = self._find_memory(result.target_memory_id)

            if target is not None:
                return target

            # The resolver named a memory that does not exist.
            if keyed_memory is None:
                return None

        return keyed_memory

    def _confirm_update(
        self,
        target: Memory,
        content: str,
        result: MemoryResolutionResult,
    ) -> bool:

        if self.confirmation is None:
            raise RuntimeError(
                "Memory confirmation is required but not configured."
            )

        return self.confirmation.confirm(
            "The new memory conflicts with an existing memory.\n\n"
            f'Existing: "{target.content}"\n'
            f'New: "{content}"\n'
            f"Reason: {result.reason}\n"
            f"Confidence: {result.confidence:.0%}\n\n"
            "Should I update the memory?"
        )

    # --------------------------------------------------
    # History
    # --------------------------------------------------

    def get_history(
        self,
        memory_id: str,
    ) -> list[MemoryVersion]:
        """Previous versions of a memory, oldest first."""

        if self.history_store is None:
            return []

        return self.history_store.get_history(memory_id)

    def restore_memory_version(
        self,
        memory_id: str,
        version: int,
    ) -> Memory:
        """
        Restore a previous version of a memory.

        History is never rewritten: the old content becomes a new
        version. Example: v1 "Python", v2 "Rust", restore v1 gives
        v3 "Python".
        """

        if version <= 0:
            raise ValueError("version must be greater than zero.")

        if self.history_store is None:
            raise RuntimeError("Memory history is not configured.")

        if self._find_memory(memory_id) is None:
            raise ValueError(f"Memory '{memory_id}' was not found.")

        historical_version = next(
            (
                item
                for item in self.history_store.get_history(memory_id)
                if item.version == version
            ),
            None,
        )

        if historical_version is None:
            raise ValueError(
                f"Version {version} was not found "
                f"for memory '{memory_id}'."
            )

        previous_version, memory = self._update(
            memory_id=memory_id,
            content=historical_version.content,
            importance=None,
            metadata=None,
        )

        self._publish(
            event_type="memory_restored",
            action="restore",
            content=memory.content,
            memory_id=memory.id,
            previous_version=previous_version,
            resulting_version=memory.version,
            reason=f"Restored version {version}.",
        )

        return memory

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------

    def forget(
        self,
        memory_id: str,
    ) -> None:
        """Permanently delete a memory by ID."""

        self.store.delete(memory_id)

        self._publish(
            event_type="memory_deleted",
            action="delete",
            content="",
            memory_id=memory_id,
        )

    def cleanup_expired(self) -> int:
        """Delete all expired memories. Returns how many were deleted."""

        expired = [
            memory
            for memory in self.store.get_all()
            if MemoryLifecycle.is_expired(memory)
        ]

        for memory in expired:
            self.forget(memory.id)

        return len(expired)

    # --------------------------------------------------
    # Internals
    # --------------------------------------------------

    def _find_memory(
        self,
        memory_id: str,
    ) -> Memory | None:

        return next(
            (
                memory
                for memory in self.store.get_all()
                if memory.id == memory_id
            ),
            None,
        )

    def _publish_decision(
        self,
        action: str,
        content: str,
        result: MemoryResolutionResult,
        memory: Memory,
        previous: int | None = None,
        resulting: int | None = None,
    ) -> None:

        self._publish(
            event_type="memory_upserted",
            action=action,
            content=content,
            memory_id=memory.id,
            resolution_result=result,
            previous_version=previous,
            resulting_version=resulting,
        )

    def _publish_failure(
        self,
        event_type: str,
        action: str,
        content: str,
        error: Exception,
        memory_id: str | None = None,
    ) -> None:

        self._publish(
            event_type=event_type,
            action=action,
            content=content,
            memory_id=memory_id,
            success=False,
            error=f"{type(error).__name__}: {error}",
        )

    def _publish(
        self,
        event_type: str,
        action: str,
        content: str,
        memory_id: str | None,
        success: bool = True,
        resolution_result: MemoryResolutionResult | None = None,
        previous_version: int | None = None,
        resulting_version: int | None = None,
        reason: str | None = None,
        error: str | None = None,
    ) -> None:

        self.event_publisher.publish(
            MemoryEvent(
                event_id=uuid4().hex,
                created_at=datetime.now(),
                event_type=event_type,
                memory_id=memory_id,
                resolution=(
                    resolution_result.resolution
                    if resolution_result is not None
                    else None
                ),
                action=action,
                # Events feed logs and the audit store: never let
                # a rejected secret reach them.
                content=self.content_guard.detector.redact(content),
                success=success,
                confidence=(
                    resolution_result.confidence
                    if resolution_result is not None
                    else None
                ),
                reason=(
                    reason
                    if reason is not None
                    else (
                        resolution_result.reason
                        if resolution_result is not None
                        else None
                    )
                ),
                previous_version=previous_version,
                resulting_version=resulting_version,
                error=error,
            )
        )
