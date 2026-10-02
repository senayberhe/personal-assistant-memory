from abc import ABC, abstractmethod


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