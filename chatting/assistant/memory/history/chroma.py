from collections.abc import Sequence
from datetime import datetime
from typing import Any

import chromadb

from assistant.memory.history.base import (
    MemoryHistoryStore,
)
from assistant.memory.history.model import MemoryVersion


class ChromaMemoryHistoryStore(
    MemoryHistoryStore
):
    """
    Persistent Chroma-backed storage for memory history.

    Each historical version is stored as a separate
    Chroma document.
    """

    def __init__(
        self,
        persist_directory: str = "data/memory",
        collection_name: str = "assistant_memory_history",
    ):
        self.client = chromadb.PersistentClient(
            path=str(persist_directory)
        )

        # History is looked up by memory ID, never by
        # meaning, so no embedding model is needed.
        # Without this, Chroma would run (and on first
        # use download) its default embedding model.
        self._collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=None,
            )
        )

    @property
    def collection(self):
        """
        Expose the underlying Chroma collection.

        This is useful for testing and future
        retrieval operations.
        """

        return self._collection

    def save_version(
        self,
        version: MemoryVersion,
    ) -> None:
        """
        Save one historical memory version.

        The combination of memory ID and version
        creates a unique history record.
        """

        history_id = (
            f"{version.memory_id}:"
            f"{version.version}"
        )

        metadata: dict[str, Any] = {
            "memory_id": version.memory_id,
            "version": version.version,
            "created_at": (
                version.created_at.isoformat()
            ),
            "recorded_at": (
                version.recorded_at.isoformat()
            ),
            "memory_key": (
                version.memory_key or ""
            ),
        }

        # History is looked up by memory_id, never by similarity,
        # so a placeholder vector is enough.
        embeddings: list[Sequence[float]] = [[0.0]]

        self._collection.upsert(
            ids=[history_id],
            documents=[version.content],
            embeddings=embeddings,
            metadatas=[metadata],
        )

    def get_history(
        self,
        memory_id: str,
    ) -> list[MemoryVersion]:
        """
        Return all historical versions for a memory.

        Versions are returned in ascending order.
        """

        if not memory_id.strip():
            return []

        results = self._collection.get(
            where={
                "memory_id": memory_id
            }
        )

        documents = results["documents"] or []

        ids = results.get(
            "ids",
            [],
        )

        metadatas = results["metadatas"] or []

        versions = []

        for index, _history_id in enumerate(ids):
            metadata: dict[str, Any] = dict(
                metadatas[index] or {}
            )

            created_at = (
                datetime.fromisoformat(
                    metadata["created_at"]
                )
            )

            recorded_at = (
                datetime.fromisoformat(
                    metadata["recorded_at"]
                )
            )

            version = MemoryVersion(
                memory_id=metadata.get(
                    "memory_id",
                    memory_id,
                ),
                version=int(
                    metadata.get(
                        "version",
                        1,
                    )
                ),
                content=documents[index],
                created_at=created_at,
                recorded_at=recorded_at,
                memory_key=(
                    metadata.get(
                        "memory_key"
                    )
                    or None
                ),
            )

            versions.append(version)

        versions.sort(
            key=lambda item: item.version
        )

        return versions