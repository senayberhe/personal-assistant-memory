from assistant.memory.confirmation import (
    MemoryConfirmation,
)


class FakeMemoryConfirmation(MemoryConfirmation):
    """
    Test double that answers every confirmation with
    a fixed value and records the questions asked.
    """

    def __init__(
        self,
        approved: bool,
    ):
        self.approved = approved
        self.messages: list[str] = []

    def confirm(
        self,
        message: str,
    ) -> bool:
        self.messages.append(message)
        return self.approved
