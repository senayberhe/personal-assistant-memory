from datetime import datetime, timedelta
from uuid import uuid4

from assistant.memory_history import (
    MemoryVersion,
)
from assistant.memory_policy import (
    MemoryPolicy,
)
from assistant.memory_lifecycle import (
    MemoryLifecycle,
)
from assistant.memory_model import (
    Memory,
    validate_importance,
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

from assistant.memory_confirmation import (
    ConsoleMemoryConfirmation,
    MemoryConfirmation,
)


class MemoryManager:
    """
    Manages the lifecycle of long-term memories.

    Responsibilities:

    - Create memories
    - Store memories
    - Retrieve memories
    - Rank memories
    - Update memories
    - Resolve memory conflicts
    - Maintain memory versions
    - Read memory history
    - Forget memories
    - Clean up expired memories
    """

    def __init__(
        self,
        store,
        retriever,
        resolver: MemoryResolverProtocol | None = None,
        history_store=None,
        policy: MemoryPolicy | None = None,
        confirmation: MemoryConfirmation | None = None,
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
        self.confirmation = (
            confirmation
            if confirmation is not None
            else ConsoleMemoryConfirmation()
        )

    # --------------------------------------------------
    # CREATE
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
        """
        Create and store a new memory.

        A new memory always starts at version 1.
        """

        if not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        importance = validate_importance(
            importance
        )

        if memory_key is not None:
            memory_key = memory_key.strip()

            if not memory_key:
                memory_key = None

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

    # --------------------------------------------------
    # FIND BY KEY
    # --------------------------------------------------

    def find_by_key(
        self,
        memory_key: str,
    ) -> list[Memory]:
        """
        Find memories using their stable memory key.
        """

        if not memory_key.strip():
            return []

        return self.store.find_by_key(
            memory_key
        )

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        importance: float | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        """
        Update an existing memory.

        Before modifying the current memory,
        its existing version is saved to the
        history store.

        Example:

            Version 1
            "I prefer Python."

            update

            Version 2
            "I prefer Rust."

        The history will retain Version 1.
        """

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

        # --------------------------------------------------
        # Validate first, so a rejected update
        # leaves no history entry behind
        # --------------------------------------------------

        if content is not None and not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        if importance is not None:
            validate_importance(importance)

        # --------------------------------------------------
        # Save current version to history
        # --------------------------------------------------

        if self.history_store is not None:
            history_version = MemoryVersion(
                memory_id=existing_memory.id,
                version=existing_memory.version,
                content=existing_memory.content,
                created_at=(
                    existing_memory.created_at
                ),
                recorded_at=datetime.now(),
                memory_key=(
                    existing_memory.memory_key
                ),
            )

            self.history_store.save_version(
                history_version
            )

        # --------------------------------------------------
        # Update content
        # --------------------------------------------------

        if content is not None:
            content = content.strip()

            if not content:
                raise ValueError(
                    "Memory content cannot be empty."
                )

            existing_memory.content = content

        # --------------------------------------------------
        # Update importance
        # --------------------------------------------------

        if importance is not None:
            existing_memory.importance = (
                validate_importance(
                    importance
                )
            )

        # --------------------------------------------------
        # Update metadata
        # --------------------------------------------------

        if metadata is not None:
            existing_memory.metadata = metadata

        # --------------------------------------------------
        # Increment version
        # --------------------------------------------------

        existing_memory.version += 1

        # --------------------------------------------------
        # Persist updated memory
        # --------------------------------------------------

        self.store.save(
            existing_memory
        )

        return existing_memory

    # --------------------------------------------------
    # UPSERT
    # --------------------------------------------------

    def upsert(
        self,
        content: str,
        memory_key: str,
        memory_type: str = "general",
        importance: float = 0.5,
        source: str = "conversation",
        metadata: dict | None = None,
        ttl_days: float | None = None,
    ) -> Memory:
        """
        Create, update, or ignore a memory.

        1. The resolver decides how the new content
           relates to the existing memory.
        2. The policy decides what to do about it.
        3. Risky updates ask for confirmation first.
        """

        if not memory_key.strip():
            raise ValueError(
                "memory_key cannot be empty."
            )

        existing_memories = self.find_by_key(
            memory_key
        )

        existing_memory = None

        if existing_memories:
            existing_memory = existing_memories[0]

        result = self.resolver.resolve(
            new_content=content,
            existing_memory=existing_memory,
        )

        decision = self.policy.decide(
            result.resolution,
            confidence=result.confidence,
        )

        if not decision.allowed:
            raise PermissionError(
                decision.reason
            )

        if decision.action == "create":
            return self.remember(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                metadata=metadata,
                ttl_days=ttl_days,
                memory_key=memory_key,
            )

        if existing_memory is None:
            raise RuntimeError(
                f"Policy requested '{decision.action}' "
                "without an existing memory."
            )

        if decision.action == "ignore":
            return existing_memory

        if decision.action == "update":

            if decision.requires_confirmation:

                if self.confirmation is None:
                    raise PermissionError(
                        "Memory update requires "
                        "confirmation."
                    )

                confirmed = self.confirmation.confirm(
                    "The new memory conflicts with an "
                    "existing memory. "
                    f'Existing: "{existing_memory.content}" '
                    f'New: "{content.strip()}". '
                    "Should I update the existing memory?"
                )

                if not confirmed:
                    return existing_memory

            return self.update_memory(
                memory_id=existing_memory.id,
                content=content,
                importance=importance,
                metadata=metadata,
            )

        raise RuntimeError(
            f"Unsupported policy action: "
            f"{decision.action}"
        )

    # --------------------------------------------------
    # RECALL
    # --------------------------------------------------

    def recall(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[Memory]:
        """
        Retrieve relevant memories that have not expired.
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

    # --------------------------------------------------
    # RANKED RECALL
    # --------------------------------------------------

    def recall_ranked(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        """
        Retrieve and rank memories using:

        - semantic similarity
        - importance
        - recency

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

    # --------------------------------------------------
    # HISTORY
    # --------------------------------------------------

    def get_history(
        self,
        memory_id: str,
    ) -> list[MemoryVersion]:
        """
        Return all historical versions of a memory.

        If no history store is configured,
        an empty list is returned.
        """

        if self.history_store is None:
            return []

        return self.history_store.get_history(
            memory_id
        )

    # --------------------------------------------------
    # ROLLBACK
    # --------------------------------------------------

    def restore_memory_version(
        self,
        memory_id: str,
        version: int,
    ) -> Memory:
        """
        Restore a previous version of a memory.

        The history is not rewritten. Instead, the
        current memory is updated with the historical
        content, which creates a new version.

        Example:

            Version 1: "I prefer Python."
            Version 2: "I prefer Rust."

            restore version 1

            Version 3: "I prefer Python."
        """

        if version <= 0:
            raise ValueError(
                "version must be greater than zero."
            )

        if self.history_store is None:
            raise RuntimeError(
                "Memory history is not configured."
            )

        existing_memory = next(
            (
                memory
                for memory in self.store.get_all()
                if memory.id == memory_id
            ),
            None,
        )

        if existing_memory is None:
            raise ValueError(
                f"Memory '{memory_id}' was not found."
            )

        historical_version = next(
            (
                item
                for item in self.history_store.get_history(
                    memory_id
                )
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

    # --------------------------------------------------
    # FORGET
    # --------------------------------------------------

    def forget(
        self,
        memory_id: str,
    ) -> None:
        """
        Permanently delete a memory by ID.
        """

        self.store.delete(
            memory_id
        )

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    def cleanup_expired(self) -> int:
        """
        Delete all expired memories.

        Returns the number of memories deleted.
        """

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
