import pytest

from assistant.memory import MemoryManager
from assistant.memory.audit.in_memory import InMemoryMemoryAuditStore
from assistant.memory.events.listener import MemoryEventListener
from assistant.memory.events.publisher import MemoryEventPublisher
from assistant.memory.guard import MemoryContentGuard, SensitiveMemoryError
from assistant.memory.history.in_memory import InMemoryHistoryStore
from assistant.memory.storage.in_memory import InMemoryStore
from tests.fakes.memory_confirmation import FakeMemoryConfirmation


class RecordingListener(MemoryEventListener):
    def __init__(self):
        self.events = []

    def handle(self, event) -> None:
        self.events.append(event)


def make_manager(**kwargs):
    listener = RecordingListener()

    manager = MemoryManager(
        store=InMemoryStore(),
        retriever=None,
        history_store=InMemoryHistoryStore(),
        confirmation=FakeMemoryConfirmation(approved=True),
        event_publisher=MemoryEventPublisher([listener]),
        **kwargs,
    )

    return manager, listener


# --------------------------------------------------
# Content guard
# --------------------------------------------------


@pytest.mark.parametrize(
    "content",
    [
        "Remember that my password is hunter2",
        "My API key is sk-proj-abcdefghijklmnopqrstuvwx",
        "My card is 4111 1111 1111 1111",
    ],
)
def test_sensitive_content_is_never_stored(content):
    manager, _ = make_manager()

    with pytest.raises(SensitiveMemoryError):
        manager.remember(content)

    with pytest.raises(SensitiveMemoryError):
        manager.upsert(content, memory_key="secret")

    assert manager.store.get_all() == []


def test_sensitive_update_is_rejected_without_history():
    manager, _ = make_manager()

    memory = manager.remember("I prefer Python.")

    with pytest.raises(SensitiveMemoryError):
        manager.update_memory(memory.id, content="password: hunter2")

    assert memory.content == "I prefer Python."
    assert manager.get_history(memory.id) == []


def test_sensitive_content_is_not_sent_to_resolver():
    class ExplodingResolver:
        def resolve(self, **kwargs):
            raise AssertionError("resolver must not see secrets")

    manager, _ = make_manager(resolver=ExplodingResolver())

    with pytest.raises(SensitiveMemoryError):
        manager.upsert("my pin is 4821")


def test_sensitive_error_is_a_value_error():
    # Existing callers that catch ValueError keep working.
    assert issubclass(SensitiveMemoryError, ValueError)


def test_overlong_content_is_rejected():
    manager, _ = make_manager(
        content_guard=MemoryContentGuard(max_characters=10)
    )

    with pytest.raises(ValueError, match="too long"):
        manager.remember("x" * 11)


def test_content_is_cleaned_before_storage():
    manager, _ = make_manager()

    memory = manager.remember("  I like\x1b tea  ")

    assert memory.content == "I like tea"


# --------------------------------------------------
# Events
# --------------------------------------------------


def test_each_operation_publishes_one_event():
    manager, listener = make_manager()

    memory = manager.remember("I prefer Python.")
    manager.update_memory(memory.id, content="I prefer Rust.")
    manager.restore_memory_version(memory.id, version=1)
    manager.forget(memory.id)

    assert [event.event_type for event in listener.events] == [
        "memory_created",
        "memory_updated",
        "memory_restored",
        "memory_deleted",
    ]

    updated = listener.events[1]
    assert (updated.previous_version, updated.resulting_version) == (1, 2)


def test_upsert_publishes_decision_with_resolution():
    manager, listener = make_manager()

    manager.upsert("I prefer Python.", memory_key="lang")
    manager.upsert("I prefer Python.", memory_key="lang")

    actions = [event.action for event in listener.events]

    assert actions == ["create", "ignore"]
    assert listener.events[1].resolution is not None
    assert listener.events[1].confidence == 1.0


def test_declined_confirmation_is_recorded():
    listener = RecordingListener()

    manager = MemoryManager(
        store=InMemoryStore(),
        retriever=None,
        confirmation=FakeMemoryConfirmation(approved=False),
        event_publisher=MemoryEventPublisher([listener]),
    )

    manager.upsert("I prefer Python.", memory_key="lang")
    manager.upsert("I don't prefer Python.", memory_key="lang")

    assert listener.events[-1].action == "update_declined"


def test_failed_operation_publishes_redacted_failure_event():
    manager, listener = make_manager()

    with pytest.raises(SensitiveMemoryError):
        manager.remember("my password is hunter2")

    [event] = listener.events

    assert event.success is False
    assert "SensitiveMemoryError" in event.error
    assert "hunter2" not in event.content


def test_audit_store_records_events_without_secrets():
    audit_store = InMemoryMemoryAuditStore()

    manager = MemoryManager(
        store=InMemoryStore(),
        retriever=None,
        audit_store=audit_store,
    )

    manager.remember("I prefer Python.")

    with pytest.raises(SensitiveMemoryError):
        manager.remember("my password is hunter2")

    records = audit_store.get_all()

    assert [record.success for record in records] == [True, False]
    assert all("hunter2" not in record.new_content for record in records)


def test_cleanup_expired_publishes_delete_events():
    manager, listener = make_manager()

    memory = manager.remember("Temporary", ttl_days=1)
    memory.expires_at = memory.created_at

    assert manager.cleanup_expired() == 1
    assert listener.events[-1].event_type == "memory_deleted"


def test_get_all_returns_active_memories_newest_first():
    manager, _ = make_manager()

    from datetime import timedelta

    first = manager.remember("First")
    second = manager.remember("Second")
    second.created_at = first.created_at + timedelta(seconds=1)
    expired = manager.remember("Expired", ttl_days=1)
    expired.expires_at = expired.created_at

    assert [memory.id for memory in manager.get_all()] == [
        second.id,
        first.id,
    ]
