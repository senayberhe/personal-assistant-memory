
from assistant.memory_manager import (
    MemoryManager,
)
from assistant.memory_model import Memory
from assistant.memory_policy import MemoryPolicy
from assistant.memory_resolver import (
    MemoryResolver,
)
from tests.fakes.memory_confirmation import (
    FakeMemoryConfirmation,
)


class FakeStore:

    def __init__(self):
        self.memories: dict[str, Memory] = {}

    def save(self, memory: Memory) -> None:
        self.memories[memory.id] = memory

    def get_all(self) -> list[Memory]:
        return list(
            self.memories.values()
        )

    def delete(self, memory_id: str) -> None:
        self.memories.pop(
            memory_id,
            None,
        )

    def find_by_key(
        self,
        memory_key: str,
    ) -> list[Memory]:

        return [
            memory
            for memory in self.memories.values()
            if memory.memory_key == memory_key
        ]


class FakeRetriever:

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ):
        return []


def create_manager(
    confirmation,
):
    store = FakeStore()

    manager = MemoryManager(
        store=store,
        retriever=FakeRetriever(),
        resolver=MemoryResolver(),
        policy=MemoryPolicy(),
        confirmation=confirmation,
    )

    return manager


def test_contradiction_requires_confirmation():

    confirmation = FakeMemoryConfirmation(
        approved=False
    )

    manager = create_manager(
        confirmation
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    result = manager.upsert(
        content="I don't prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    assert result.id == memory.id

    assert (
        result.content
        == "I prefer Python."
    )

    assert len(
        confirmation.messages
    ) == 1


def test_confirmed_contradiction_updates():

    confirmation = FakeMemoryConfirmation(
        approved=True
    )

    manager = create_manager(
        confirmation
    )

    memory = manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    result = manager.upsert(
        content="I don't prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    assert result.id == memory.id

    assert (
        result.content
        == "I don't prefer Python."
    )

    assert result.version == 2

    assert len(
        confirmation.messages
    ) == 1


def test_confirmation_message_is_recorded():

    confirmation = FakeMemoryConfirmation(
        approved=False
    )

    manager = create_manager(
        confirmation
    )

    manager.remember(
        content="I prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    manager.upsert(
        content="I don't prefer Python.",
        memory_key=(
            "preferred_programming_language"
        ),
    )

    message = (
        confirmation.messages[0]
    )

    assert "conflicts" in (
        message.lower()
    )

    assert "update" in (
        message.lower()
    )

def test_uncertain_update_asks_before_changing():
    confirmation = FakeMemoryConfirmation(approved=False)

    manager = create_manager(confirmation)

    manager.remember(
        content="I prefer Python.",
        memory_key="preferred_programming_language",
    )

    result = manager.upsert(
        content="I now prefer Rust.",
        memory_key="preferred_programming_language",
    )

    assert result.content == "I prefer Python."
    assert result.version == 1
    assert "I now prefer Rust." in confirmation.messages[0]


def test_unrelated_content_creates_without_asking():
    confirmation = FakeMemoryConfirmation(approved=False)

    manager = create_manager(confirmation)

    manager.remember(content="I prefer Python.", memory_key="topic")

    manager.upsert(content="My favorite color is blue.", memory_key="topic")

    assert confirmation.messages == []
    assert len(manager.find_by_key("topic")) == 2
