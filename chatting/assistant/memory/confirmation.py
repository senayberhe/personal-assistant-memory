from abc import ABC, abstractmethod
from collections.abc import Callable


class MemoryConfirmation(ABC):
    """
    Interface for confirming potentially sensitive
    memory changes.
    """
    @abstractmethod
    def confirm(self, message: str) -> bool:
        pass


class ConsoleMemoryConfirmation(MemoryConfirmation):
    """
    Console-based confirmation implementation.
    This is useful during development and testing.
    """

    def confirm(
        self,
        message: str,
    ) -> bool:
        answer = input(f"\n{message} [y/N]:")
        return answer.strip().lower() in {
            "y",
            "yes",
        }


class CallbackMemoryConfirmation(MemoryConfirmation):
    """
    Adapts any `confirm(question) -> bool` function.

    Lets the memory system reuse the UI's own yes/no prompt
    (for example the rich text chat) instead of input().
    """

    def __init__(
        self,
        confirm: Callable[[str], bool],
    ):
        self._confirm = confirm

    def confirm(
        self,
        message: str,
    ) -> bool:
        return self._confirm(message)
