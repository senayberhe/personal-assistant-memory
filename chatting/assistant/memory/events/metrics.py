from dataclasses import dataclass


@dataclass
class MemoryMetrics:
    """
    Tracks memory lifecycle operations.
    """

    created: int = 0
    updated: int = 0
    ignored: int = 0
    contradicted: int = 0
    failed: int = 0

    def record(
        self,
        action: str,
        success: bool,
    ) -> None:

        if not success:
            self.failed += 1
            return

        if action == "create":
            self.created += 1

        elif action == "update":
            self.updated += 1

        elif action == "ignore":
            self.ignored += 1

        elif action == "contradict":
            self.contradicted += 1

    def snapshot(self) -> dict:
        return {
            "created": self.created,
            "updated": self.updated,
            "ignored": self.ignored,
            "contradicted": self.contradicted,
            "failed": self.failed,
        }