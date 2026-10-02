from datetime import datetime

from assistant.memory.audit.chroma import (
    ChromaMemoryAuditStore,
)
from assistant.memory.audit.record import (
    MemoryAuditRecord,
)


def create_record(
    record_id: str,
    memory_id: str = "memory-1",
) -> MemoryAuditRecord:

    return MemoryAuditRecord(
        record_id=record_id,
        created_at=datetime.now(),
        new_content="I prefer Python.",
        resolution="UPDATE",
        action="update",
        target_memory_id=memory_id,
        confidence=0.95,
        reason="The new memory is related.",
        similarity=0.92,
        ranking_score=0.88,
        confirmation_required=False,
        confirmed=False,
        success=True,
        previous_version=1,
        resulting_version=2,
    )


def test_save_and_get(tmp_path):

    store = ChromaMemoryAuditStore(
        persist_directory=str(tmp_path),
        collection_name="test_audit",
    )

    record = create_record("audit-1")

    store.save(record)

    records = store.get_all()

    assert len(records) == 1

    assert records[0].record_id == "audit-1"
    assert (
        records[0].new_content
        == "I prefer Python."
    )
    assert (
        records[0].target_memory_id
        == "memory-1"
    )
    assert records[0].success is True


def test_get_by_memory_id(tmp_path):

    store = ChromaMemoryAuditStore(
        persist_directory=str(tmp_path),
        collection_name="test_audit",
    )

    store.save(
        create_record(
            "audit-1",
            "memory-1",
        )
    )

    store.save(
        create_record(
            "audit-2",
            "memory-2",
        )
    )

    records = store.get_by_memory_id(
        "memory-1"
    )

    assert len(records) == 1
    assert records[0].record_id == "audit-1"


def test_persistence_between_instances(
    tmp_path,
):

    first_store = ChromaMemoryAuditStore(
        persist_directory=str(tmp_path),
        collection_name="persistent_audit",
    )

    first_store.save(
        create_record("audit-1")
    )

    second_store = ChromaMemoryAuditStore(
        persist_directory=str(tmp_path),
        collection_name="persistent_audit",
    )

    records = second_store.get_all()

    assert len(records) == 1
    assert records[0].record_id == "audit-1"


def test_unknown_memory_returns_empty(
    tmp_path,
):

    store = ChromaMemoryAuditStore(
        persist_directory=str(tmp_path),
        collection_name="test_audit",
    )

    records = store.get_by_memory_id(
        "does-not-exist"
    )

    assert records == []