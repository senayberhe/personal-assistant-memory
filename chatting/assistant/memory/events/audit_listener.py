from assistant.memory.audit.record import (
    MemoryAuditRecord,
)

from assistant.memory.audit.base import (
    MemoryAuditStore,
)

from assistant.memory.events.event import (
    MemoryEvent,
)

from assistant.memory.events.listener import (
    MemoryEventListener,
)


class MemoryAuditListener(
    MemoryEventListener
):
    """
    Converts memory events into persistent
    audit records.
    """

    def __init__(
        self,
        audit_store: MemoryAuditStore,
    ):
        self.audit_store = audit_store

    def handle(
        self,
        event: MemoryEvent,
    ) -> None:

        record = MemoryAuditRecord(
            record_id=event.event_id,
            created_at=event.created_at,
            new_content=event.content,
            resolution=(
                event.resolution.value
                if event.resolution is not None
                else ""
            ),
            action=event.action,
            target_memory_id=event.memory_id,
            confidence=(
                event.confidence
                if event.confidence is not None
                else 0.0
            ),
            reason=event.reason or "",
            success=event.success,
            previous_version=(
                event.previous_version
            ),
            resulting_version=(
                event.resulting_version
            ),
            error=event.error,
        )

        self.audit_store.save(record)