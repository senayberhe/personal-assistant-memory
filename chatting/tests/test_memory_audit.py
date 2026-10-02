from datetime import datetime

from assistant.in_memory_memory_audit_store import (
    InMemoryMemoryAuditStore,
)
from assistant.memory_audit import (
    MemoryAuditRecord,
)


def create_record(
    record_id: str,
) -> MemoryAuditRecord:

    return MemoryAuditRecord(
        record_id=record_id,
        created_at=datetime.now(),
        new_content="I prefer Python.",
        resolution="CREATE",
        action="create",
        target_memory_id=None,
        confidence=1.0,
        reason="No existing memory.",
    )


def test_audit_record_is_saved():

    store = InMemoryMemoryAuditStore()

    record = create_record(
        "audit-1"
    )

    store.save(record)

    records = store.get_all()

    assert len(records) == 1
    assert records[0] == record


def test_audit_store_keeps_multiple_records():

    store = InMemoryMemoryAuditStore()

    first = create_record("audit-1")
    second = create_record("audit-2")

    store.save(first)
    store.save(second)

    records = store.get_all()

    assert len(records) == 2
    assert records[0].record_id == "audit-1"
    assert records[1].record_id == "audit-2"


def test_get_all_returns_copy():

    store = InMemoryMemoryAuditStore()

    record = create_record("audit-1")

    store.save(record)

    records = store.get_all()

    records.clear()

    assert len(store.get_all()) == 1