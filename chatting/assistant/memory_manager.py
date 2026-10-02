from datetime import datetime, timedelta
from uuid import uuid4

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
from assistant.memory_ranking import (
    rank_memories,
)
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolver import (
    MemoryResolver,
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
        resolver: MemoryResolver | None = None,
        history_store=None,
    ):
        self.store = store

        self.retriever = retriever

        self.resolver = (
            resolver
            if resolver is not None
            else MemoryResolver()
        )

        self.history_store = history_store

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

        CREATE:
            No memory exists with this key.

        UPDATE:
            A memory exists with this key,
            but its content is different.

        IGNORE:
            The existing memory already contains
            the same information.
        """

        if not memory_key.strip():
            raise ValueError(
                "memory_key cannot be empty."
            )

        existing_memories = (
            self.find_by_key(
                memory_key
            )
        )

        existing_memory = None

        if existing_memories:
            existing_memory = (
                existing_memories[0]
            )

        resolution = (
            self.resolver.resolve(
                new_content=content,
                existing_memory=existing_memory,
            )
        )

        # --------------------------------------------------
        # CREATE
        # --------------------------------------------------

        if (
            resolution
            == MemoryResolution.CREATE
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

        # --------------------------------------------------
        # UPDATE
        # --------------------------------------------------

        if (
            resolution
            == MemoryResolution.UPDATE
        ):
            if existing_memory is None:
                raise RuntimeError(
                    "Resolver requested UPDATE "
                    "without an existing memory."
                )

            return self.update_memory(
                memory_id=existing_memory.id,
                content=content,
                importance=importance,
                metadata=metadata,
            )

        # --------------------------------------------------
        # IGNORE
        # --------------------------------------------------

        if (
            resolution
            == MemoryResolution.IGNORE
            and existing_memory is not None
        ):
            return existing_memory

        raise RuntimeError(
            f"Unknown memory resolution: "
            f"{resolution}"
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
