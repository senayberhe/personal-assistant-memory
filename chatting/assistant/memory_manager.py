from datetime import datetime, timedelta
from uuid import uuid4


from assistant.memory_audit import (
    MemoryAuditRecord,
)

from assistant.memory_audit_store import (
    MemoryAuditStore,
)


from assistant.memory_candidate import (
    MemoryCandidate,
)
from assistant.memory_candidate_retriever import (
    MemoryCandidateRetriever,
)
from assistant.memory_candidate_ranker import (
    MemoryCandidateRanker,
)
from assistant.memory_confirmation import (
    MemoryConfirmation,
)
from assistant.memory_history import (
    MemoryVersion,
)
from assistant.memory_lifecycle import (
    MemoryLifecycle,
)
from assistant.memory_model import (
    Memory,
    validate_importance,
)
from assistant.memory_policy import (
    MemoryPolicy,
)
from assistant.memory_ranking import (
    rank_memories,
)
from assistant.memory_resolver import (
    MemoryResolver,
)
from assistant.memory_resolver_protocol import (
    MemoryResolverProtocol,
)


class MemoryManager:
    """
    Coordinates memory creation, retrieval, resolution,
    updates, history, rollback, and deletion.

    The MemoryManager owns the memory workflow but
    delegates storage, retrieval, resolution, policy,
    and confirmation to specialized components.
    """

    def __init__(
        self,
        store,
        retriever,
        resolver: MemoryResolverProtocol | None = None,
        history_store=None,
        policy: MemoryPolicy | None = None,
        confirmation: MemoryConfirmation | None = None,
        candidate_retriever: (
            MemoryCandidateRetriever | None
        ) = None,
        candidate_ranker: (
            MemoryCandidateRanker | None
        ) = None,
        audit_store: MemoryAuditStore | None = None,
    ):
        self.store = store
        self.retriever = retriever

        self.resolver = (
            resolver
            if resolver is not None
            else MemoryResolver()
        )

        self.history_store = history_store

        self.policy = (
            policy
            if policy is not None
            else MemoryPolicy()
        )

        self.confirmation = confirmation

        self.candidate_retriever = (
            candidate_retriever
        )

        self.candidate_ranker = (
            candidate_ranker
            if candidate_ranker is not None
            else MemoryCandidateRanker()
        )
        self.audit_store = audit_store

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

        if not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        importance = validate_importance(
            importance
        )

        if memory_key is not None:
            memory_key = memory_key.strip() or None

        created_at = datetime.now()

        expires_at = None

        if ttl_days is not None:

            if ttl_days <= 0:
                raise ValueError(
                    "ttl_days must be greater than zero."
                )

            expires_at = (
                created_at
                + timedelta(days=ttl_days)
            )

        memory = Memory(
            id=uuid4().hex,
            content=content.strip(),
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

    def find_by_key(
        self,
        memory_key: str,
    ) -> list[Memory]:

        if not memory_key.strip():
            return []

        return self.store.find_by_key(
            memory_key
        )

    def retrieve_candidates(
        self,
        query: str,
        candidate_limit: int = 20,
        top_k: int = 5,
    ):
        """
        Retrieve and rerank memory candidates.

        Stage 1:
            Retrieve candidate_limit memories.

        Stage 2:
            Rerank candidates.

        Stage 3:
            Return top_k candidates.
        """

        if self.candidate_retriever is None:
            return []

        if not query.strip():
            return []

        if candidate_limit <= 0:
            return []

        if top_k <= 0:
            return []

        candidates = (
            self.candidate_retriever
            .retrieve_candidates(
                query=query,
                candidate_limit=candidate_limit,
            )
        )

        return self.candidate_ranker.rank(
            candidates,
            top_k=top_k,
        )

    def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        importance: float | None = None,
        metadata: dict | None = None,
    ) -> Memory:

        memories = self.store.get_all()

        existing_memory = next(
            (
                memory
                for memory in memories
                if memory.id == memory_id
            ),
            None,
        )

        if existing_memory is None:
            raise ValueError(
                f"Memory '{memory_id}' was not found."
            )

        # Validate first, so a rejected update
        # leaves no history entry behind.
        if content is not None and not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        if importance is not None:
            validate_importance(importance)

        if self.history_store is not None:

            history_version = MemoryVersion(
                memory_id=existing_memory.id,
                version=existing_memory.version,
                content=existing_memory.content,
                created_at=existing_memory.created_at,
                recorded_at=datetime.now(),
                memory_key=(
                    existing_memory.memory_key
                ),
            )

            self.history_store.save_version(
                history_version
            )

        if content is not None:

            content = content.strip()

            if not content:
                raise ValueError(
                    "Memory content cannot be empty."
                )

            existing_memory.content = content

        if importance is not None:

            existing_memory.importance = (
                validate_importance(
                    importance
                )
            )

        if metadata is not None:
            existing_memory.metadata = metadata

        existing_memory.version += 1

        self.store.save(
            existing_memory
        )

        return existing_memory

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

        if not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        # memory_key is optional, but an explicitly
        # blank key is almost certainly a mistake.
        if memory_key is not None and not memory_key.strip():
            raise ValueError(
                "memory_key cannot be empty."
            )

        existing_memory = None

        if memory_key:
            memories = self.find_by_key(
                memory_key
            )

            if memories:
                existing_memory = memories[0]

        candidates = self.retrieve_candidates(
            query=content,
            candidate_limit=candidate_limit,
            top_k=top_k,
        )

        # A memory with the same key is the strongest
        # candidate even if semantic search ranked it
        # low or missed it, so make sure it comes first.
        if existing_memory is not None:
            candidates = [
                MemoryCandidate(
                    memory=existing_memory,
                    similarity=1.0,
                    ranking_score=1.0,
                ),
                *(
                    candidate
                    for candidate in candidates
                    if candidate.memory.id
                    != existing_memory.id
                ),
            ]

        resolution_result = (
            self.resolver.resolve(
                new_content=content,
                existing_memory=existing_memory,
                candidates=candidates,
            )
        )

        decision = self.policy.decide(
            resolution=(
                resolution_result.resolution
            ),
            confidence=(
                resolution_result.confidence
            ),
        )

        if not decision.allowed:
            raise PermissionError(
                decision.reason
            )

        if (
            decision.action == "ignore"
        ):
            target_id = (
                resolution_result.target_memory_id
            )

            if target_id:
                memories = self.store.get_all()

                existing = next(
                    (
                        memory
                        for memory in memories
                        if memory.id == target_id
                    ),
                    None,
                )

                if existing is not None:
                    return existing

            if existing_memory is not None:
                return existing_memory

            return self.remember(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                metadata=metadata,
                ttl_days=ttl_days,
                memory_key=memory_key,
            )

        if (
            decision.action == "create"
        ):
            return self.remember(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                metadata=metadata,
                ttl_days=ttl_days,
                memory_key=memory_key,
            )

        if (
            decision.action == "update"
        ):
            target_memory_id = (
                resolution_result.target_memory_id
            )

            if target_memory_id is None:
                raise ValueError(
                    "Memory update requires a "
                    "target memory."
                )

            memories = self.store.get_all()

            target_memory = next(
                (
                    memory
                    for memory in memories
                    if memory.id == target_memory_id
                ),
                None,
            )

            if target_memory is None:
                raise ValueError(
                    f"Target memory "
                    f"'{target_memory_id}' "
                    "was not found."
                )

            if (
                decision.requires_confirmation
            ):

                if self.confirmation is None:
                    raise RuntimeError(
                        "Memory confirmation is "
                        "required but not configured."
                    )

                confirmation_message = (
                    "The new memory conflicts with an "
                    "existing memory.\n\n"
                    f'Existing: "{target_memory.content}"\n'
                    f'New: "{content.strip()}"\n'
                    f"Reason: "
                    f"{resolution_result.reason}\n"
                    f"Confidence: "
                    f"{resolution_result.confidence:.0%}\n\n"
                    "Should I update the memory?"
                )

                approved = (
                    self.confirmation.confirm(
                        confirmation_message
                    )
                )

                if not approved:
                    return target_memory

            return self.update_memory(
                memory_id=target_memory.id,
                content=content,
                importance=importance,
                metadata=metadata,
            )

        raise RuntimeError(
            "Unsupported memory policy action: "
            f"{decision.action}"
        )

    def recall(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[Memory]:
        """
        Retrieve relevant memories that have not expired.

        retriever.retrieve() already returns Memory
        objects (not scored results).
        """

        memories = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            memory_type=memory_type,
        )

        return MemoryLifecycle.filter_active(
            memories
        )

    def recall_scored(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        """
        Retrieve non-expired memories together with
        their similarity scores (RetrievedMemory objects).
        """

        results = self.retriever.retrieve_scored(
            query,
            top_k=top_k,
            memory_type=memory_type,
        )

        return [
            result
            for result in results
            if not MemoryLifecycle.is_expired(
                result.memory
            )
        ]

    def recall_ranked(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        """
        Retrieve and rank memories by similarity,
        importance, and recency.

        Extra candidates are fetched by similarity so
        that importance and recency can reorder them.
        """

        results = self.recall_scored(
            query,
            top_k=top_k * 3,
            memory_type=memory_type,
        )

        return rank_memories(
            results
        )[:top_k]

    def get_history(
        self,
        memory_id: str,
    ):

        if self.history_store is None:
            return []

        return self.history_store.get_history(
            memory_id
        )

    def restore_memory_version(
        self,
        memory_id: str,
        version: int,
    ) -> Memory:

        if version <= 0:
            raise ValueError(
                "version must be greater than zero."
            )

        if self.history_store is None:
            raise RuntimeError(
                "Memory history is not configured."
            )

        memories = self.store.get_all()

        existing_memory = next(
            (
                memory
                for memory in memories
                if memory.id == memory_id
            ),
            None,
        )

        if existing_memory is None:
            raise ValueError(
                f"Memory '{memory_id}' was not found."
            )

        history = self.history_store.get_history(
            memory_id
        )

        historical_version = next(
            (
                item
                for item in history
                if item.version == version
            ),
            None,
        )

        if historical_version is None:
            raise ValueError(
                f"Version {version} was not found "
                f"for memory '{memory_id}'."
            )

        return self.update_memory(
            memory_id=memory_id,
            content=historical_version.content,
        )

    def forget(
        self,
        memory_id: str,
    ) -> None:

        self.store.delete(
            memory_id
        )

    def cleanup_expired(self) -> int:

        memories = self.store.get_all()

        expired = [
            memory
            for memory in memories
            if MemoryLifecycle.is_expired(
                memory
            )
        ]

        for memory in expired:
            self.store.delete(
                memory.id
            )

        return len(expired)
