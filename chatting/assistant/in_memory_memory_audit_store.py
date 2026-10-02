from assistant.memory_audit import (
    MemoryAuditRecord,
)

from assistant.memory_audit_store import (
    MemoryAuditStore,
)


class InMemoryMemoryAuditStore(
    MemoryAuditStore
):

    def __init__(self):
        self.records: list[
            MemoryAuditRecord
        ] = []

    def save(
        self,
        record: MemoryAuditRecord,
    ) -> None:

        self.records.append(record)

    def get_all(
        self,
    ) -> list[MemoryAuditRecord]:

        return list(self.records)

    def get_by_memory_id(
        self,
        memory_id: str,
    ) -> list[MemoryAuditRecord]:

        if not memory_id.strip():
            return []

        return [
            record
            for record in self.records
            if record.target_memory_id
            == memory_id
        ]