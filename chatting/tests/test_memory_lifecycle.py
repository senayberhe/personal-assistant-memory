from datetime import datetime, timedelta

from assistant.memory import Memory
from assistant.memory_lifecycle import (
    MemoryLifecycle,
)


def test_memory_without_expiration_is_not_expired():
    """
    A memory with expires_at=None should never expire.
    """

    now = datetime.now()

    memory = Memory(
        id="1",
        content="I am learning Python.",
        created_at=now,
        expires_at=None,
    )

    assert not MemoryLifecycle.is_expired(
        memory,
        now=now,
    )


def test_future_expiration_is_not_expired():
    """
    A memory whose expiration date is in the future
    should still be active.
    """

    now = datetime.now()

    memory = Memory(
        id="2",
        content="Temporary memory",
        created_at=now,
        expires_at=now + timedelta(days=7),
    )

    assert not MemoryLifecycle.is_expired(
        memory,
        now=now,
    )


def test_past_expiration_is_expired():
    """
    A memory whose expiration date is in the past
    should be considered expired.
    """

    now = datetime.now()

    memory = Memory(
        id="3",
        content="Expired memory",
        created_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=1),
    )

    assert MemoryLifecycle.is_expired(
        memory,
        now=now,
    )


def test_memory_expiring_now_is_expired():
    """
    A memory is expired when now == expires_at.
    """

    now = datetime.now()

    memory = Memory(
        id="4",
        content="Expiring memory",
        created_at=now,
        expires_at=now,
    )

    assert MemoryLifecycle.is_expired(
        memory,
        now=now,
    )


def test_filter_active_memories():
    """
    filter_active() should remove expired memories
    while keeping active and permanent memories.
    """

    now = datetime.now()

    active = Memory(
        id="active",
        content="Active memory",
        created_at=now,
        expires_at=now + timedelta(days=7),
    )

    expired = Memory(
        id="expired",
        content="Expired memory",
        created_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=1),
    )

    permanent = Memory(
        id="permanent",
        content="Permanent memory",
        created_at=now,
        expires_at=None,
    )

    result = MemoryLifecycle.filter_active(
        [
            active,
            expired,
            permanent,
        ],
        now=now,
    )

    ids = {
        memory.id
        for memory in result
    }

    assert ids == {
        "active",
        "permanent",
    }


def test_cleanup_expired_memories():
    """
    cleanup_expired() should return the IDs
    of expired memories.
    """

    now = datetime.now()

    expired = Memory(
        id="expired",
        content="Old temporary memory",
        created_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=1),
    )

    active = Memory(
        id="active",
        content="Active memory",
        created_at=now,
        expires_at=now + timedelta(days=10),
    )

    memories = [
        expired,
        active,
    ]

    expired_ids = MemoryLifecycle.cleanup_expired(
        memories,
        now=now,
    )

    assert expired_ids == [
        "expired"
    ]