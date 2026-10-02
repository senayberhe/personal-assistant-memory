from datetime import datetime

from assistant.memory import Memory


def test_memory_has_memory_key():
    memory = Memory(
        id = "1",
        content = "I prefer Python.",
        created_at = datetime.now(),
        memory_type = "preference",
        memory_key = "preferred_programming_language"
    )

    assert(
        memory.memory_key =="preferred_programming_language"
    )

def test_memory_key_can_be_none():
    memory = Memory(
        id = "2",
        content = "I like JavaScript.",
        created_at = datetime.now(),
        memory_type = "preference",
        memory_key = None
    )

    assert(
        memory.memory_key is None
    )


def test_memory_key_is_stored_separately_from_content():
    memory = Memory(
        id = "3",
        content = "I prefer Python.",
        created_at = datetime.now(),
        memory_type = "preference",
        memory_key = "preferred_programming_language"
    )

    assert memory.content=="I prefer Python."
    assert memory.memory_key=="preferred_programming_language"
