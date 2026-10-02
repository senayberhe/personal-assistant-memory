from unittest.mock import MagicMock

from assistant.memory_audit import (
    MemoryAuditRecord,
)


def test_audit_record_can_be_saved_after_update():

    audit_store = MagicMock()

    record = MemoryAuditRecord(
        record_id="audit-1",
        created_at=MagicMock(),
        new_content=(
            "I don't prefer Python anymore."
        ),
        resolution="CONTRADICT",
        action="update",
        target_memory_id="memory-1",
        confidence=0.98,
        reason=(
            "The new memory contradicts "
            "the existing preference."
        ),
        similarity=0.96,
        ranking_score=0.91,
        confirmation_required=True,
        confirmed=True,
        success=True,
        previous_version=1,
        resulting_version=2,
    )

    audit_store.save(record)

    audit_store.save.assert_called_once_with(
        record
    )