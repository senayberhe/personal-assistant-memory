from datetime import datetime

import chromadb

from assistant.memory_audit import (
    MemoryAuditRecord,
)

from assistant.memory_audit_store import (
    MemoryAuditStore,
)


class ChromaMemoryAuditStore(
    MemoryAuditStore
):
    """
    Persistent Chroma-backed audit storage.

    Each audit record is stored as one document.
    """

    def __init__(
        self,
        persist_directory: str = "data/memory",
        collection_name: str = "assistant_memory_audit",
    ):
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self._collection = (
            self.client.get_or_create_collection(
                name=collection_name
            )
        )

    @property
    def collection(self):
        return self._collection

    def save(
        self,
        record: MemoryAuditRecord,
    ) -> None:

        metadata = {
            "created_at": (
                record.created_at.isoformat()
            ),
            "resolution": record.resolution,
            "action": record.action,
            "target_memory_id": (
                record.target_memory_id
                or ""
            ),
            "confidence": record.confidence,
            "similarity": (
                record.similarity
                if record.similarity is not None
                else -1.0
            ),
            "ranking_score": (
                record.ranking_score
                if record.ranking_score is not None
                else -1.0
            ),
            "confirmation_required": (
                record.confirmation_required
            ),
            "confirmed": record.confirmed,
            "success": record.success,
            "error": record.error or "",
            "previous_version": (
                record.previous_version
                if record.previous_version is not None
                else -1
            ),
            "resulting_version": (
                record.resulting_version
                if record.resulting_version is not None
                else -1
            ),
        }

        self._collection.upsert(
            ids=[record.record_id],
            documents=[record.new_content],
            metadatas=[metadata],
        )

    def get_all(
        self,
    ) -> list[MemoryAuditRecord]:

        results = self._collection.get()

        return self._build_records(results)

    def get_by_memory_id(
        self,
        memory_id: str,
    ) -> list[MemoryAuditRecord]:

        if not memory_id.strip():
            return []

        results = self._collection.get(
            where={
                "target_memory_id": memory_id
            }
        )

        records = self._build_records(
            results
        )

        records.sort(
            key=lambda record: record.created_at
        )

        return records

    @staticmethod
    def _build_records(
        results,
    ) -> list[MemoryAuditRecord]:

        documents = results.get(
            "documents",
            [],
        )

        ids = results.get(
            "ids",
            [],
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        records = []

        for index, record_id in enumerate(
            ids
        ):

            metadata = (
                metadatas[index]
                or {}
            )

            created_at = (
                datetime.fromisoformat(
                    metadata["created_at"]
                )
            )

            target_memory_id = (
                metadata.get(
                    "target_memory_id"
                )
                or None
            )

            similarity = (
                float(
                    metadata["similarity"]
                )
                if float(
                    metadata.get(
                        "similarity",
                        -1.0,
                    )
                ) >= 0
                else None
            )

            ranking_score = (
                float(
                    metadata["ranking_score"]
                )
                if float(
                    metadata.get(
                        "ranking_score",
                        -1.0,
                    )
                ) >= 0
                else None
            )

            previous_version = (
                int(
                    metadata[
                        "previous_version"
                    ]
                )
                if int(
                    metadata.get(
                        "previous_version",
                        -1,
                    )
                ) >= 0
                else None
            )

            resulting_version = (
                int(
                    metadata[
                        "resulting_version"
                    ]
                )
                if int(
                    metadata.get(
                        "resulting_version",
                        -1,
                    )
                ) >= 0
                else None
            )

            records.append(
                MemoryAuditRecord(
                    record_id=record_id,
                    created_at=created_at,
                    new_content=documents[index],
                    resolution=metadata[
                        "resolution"
                    ],
                    action=metadata[
                        "action"
                    ],
                    target_memory_id=(
                        target_memory_id
                    ),
                    confidence=float(
                        metadata[
                            "confidence"
                        ]
                    ),
                    reason=metadata.get(
                        "reason",
                        "",
                    ),
                    similarity=similarity,
                    ranking_score=ranking_score,
                    confirmation_required=(
                        bool(
                            metadata.get(
                                "confirmation_required",
                                False,
                            )
                        )
                    ),
                    confirmed=bool(
                        metadata.get(
                            "confirmed",
                            False,
                        )
                    ),
                    success=bool(
                        metadata.get(
                            "success",
                            False,
                        )
                    ),
                    error=(
                        metadata.get(
                            "error"
                        )
                        or None
                    ),
                    previous_version=(
                        previous_version
                    ),
                    resulting_version=(
                        resulting_version
                    ),
                )
            )

        return records