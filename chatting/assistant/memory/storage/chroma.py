from collections.abc import Sequence
from datetime import datetime

import chromadb

from assistant.memory.embeddings import EmbeddingService
from assistant.memory.model import Memory
from assistant.memory.storage.base import MemoryStore


def memory_to_metadata(memory: Memory) -> dict:
    """Convert a Memory into Chroma metadata.

    Chroma metadata values cannot be None, so optional
    fields are only written when they are set.
    """

    metadata: dict = {
        "created_at": memory.created_at.isoformat(),
        "memory_type": memory.memory_type,
        "importance": memory.importance,
        "source": memory.source,
        "memory_key": memory.memory_key,
        "version": memory.version,
    }

    if memory.expires_at is not None:
        metadata["expires_at"] = memory.expires_at.isoformat()

    if memory.memory_key is not None:
        metadata["memory_key"] = memory.memory_key

    return metadata


def memory_from_chroma(
    memory_id: str,
    content: str,
    metadata: dict | None,
) -> Memory:
    """Rebuild a Memory from a Chroma row."""

    metadata = metadata or {}

    expires_at = metadata.get("expires_at")

    return Memory(
        id=memory_id,
        content=content,
        created_at=datetime.fromisoformat(
            metadata["created_at"]
        ),
        memory_type=metadata.get(
            "memory_type",
            "general",
        ),
        importance=float(
            metadata.get(
                "importance",
                0.5,
            )
        ),
        source=metadata.get(
            "source",
            "conversation",
        ),
        expires_at=(
            datetime.fromisoformat(expires_at)
            if expires_at
            else None
        ),
        memory_key=metadata.get(
            "memory_key"
        ),
        version=int(
            metadata.get(
                "version",
                1,
            )
        ),
    )


class ChromaMemoryStore(MemoryStore):

    def __init__(
        self,
        persist_directory: str = "data/memory",
        collection_name: str = "assistant_memories",
        embedding_service: EmbeddingService | None = None,
    ):
        # Must match the service used by the retriever,
        # otherwise query and stored vectors differ in size.
        self.embedding_service = embedding_service

        self.client = chromadb.PersistentClient(
            path=str(persist_directory)
        )

        self._collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                configuration={
                    "hnsw": {"space": "cosine"}
                },
            )
        )

    @property
    def collection(self): return self._collection

    def save(self, memory: Memory) -> None:
        embeddings: list[Sequence[float]] | None = None

        if self.embedding_service is not None:
            embeddings = [
                self.embedding_service.embed(memory.content)
            ]

        self._collection.upsert(
            ids=[memory.id],
            documents=[memory.content],
            embeddings=embeddings,
            metadatas=[
                memory_to_metadata(memory)
            ],
        )

    def get_all(self) -> list[Memory]:
        return self._to_memories(
            self._collection.get()
        )

    def get(self, memory_id: str) -> Memory | None:
        memories = self._to_memories(
            self._collection.get(
                ids=[memory_id]
            )
        )

        return memories[0] if memories else None

    def find_by_key(self, memory_key: str) -> list[Memory]:
        if not memory_key.strip():
            return []

        return self._to_memories(
            self._collection.get(
                where={
                    "memory_key": memory_key
                }
            )
        )

    def delete(self, memory_id: str) -> None:
        self._collection.delete(
            ids=[memory_id]
        )

    @staticmethod
    def _to_memories(results) -> list[Memory]:
        ids = results.get("ids") or []
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []

        return [
            memory_from_chroma(
                memory_id,
                documents[index],
                metadatas[index],
            )
            for index, memory_id in enumerate(ids)
        ]
