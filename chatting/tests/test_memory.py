from assistant.memory import (
    ConversationMemory,
)


def test_memory_stores_message():

    memory = ConversationMemory()

    memory.add_user_message(
        "Hello"
    )

    messages = (
        memory.get_messages()
    )

    assert len(messages) == 1

    assert (
        messages[0]["role"]
        == "user"
    )

    assert (
        messages[0]["content"]
        == "Hello"
    )


def test_memory_keeps_recent_messages():

    memory = ConversationMemory(
        max_messages=3
    )

    memory.add_user_message("one")
    memory.add_user_message("two")
    memory.add_user_message("three")
    memory.add_user_message("four")

    messages = (
        memory.get_messages()
    )

    assert len(messages) == 3

    assert (
        messages[0]["content"]
        == "two"
    )

    assert (
        messages[-1]["content"]
        == "four"
    )