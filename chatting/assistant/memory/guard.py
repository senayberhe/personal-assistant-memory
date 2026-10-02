"""Checks applied to memory content before it is stored."""

from assistant.safety import SensitiveDataDetector, clean_text

DEFAULT_MAX_MEMORY_CHARACTERS = 1000


class SensitiveMemoryError(ValueError):
    """Raised when memory content contains sensitive data."""

    def __init__(
        self,
        kinds: list[str],
    ):
        self.kinds = kinds

        super().__init__(
            "Refusing to store sensitive data in memory "
            f"({', '.join(kinds)})."
        )


class MemoryContentGuard:
    """
    Validates and normalizes memory content.

    Long-term memory is persisted to disk and sent back to the
    model in later conversations, so secrets must never enter it.
    """

    def __init__(
        self,
        max_characters: int = DEFAULT_MAX_MEMORY_CHARACTERS,
        detector: SensitiveDataDetector | None = None,
    ):
        if max_characters <= 0:
            raise ValueError("max_characters must be greater than zero.")

        self.max_characters = max_characters
        self.detector = detector or SensitiveDataDetector()

    def check(
        self,
        content: str,
    ) -> str:
        """
        Return cleaned content, or raise ValueError.

        Raises SensitiveMemoryError (a ValueError) when the content
        contains secrets.
        """

        # Clean a little past the limit, so "too long" can be
        # detected instead of silently truncated.
        cleaned = clean_text(content, self.max_characters + 1)

        if not cleaned:
            raise ValueError("Memory content cannot be empty.")

        if len(cleaned) > self.max_characters:
            raise ValueError(
                "Memory content is too long "
                f"(maximum {self.max_characters} characters)."
            )

        kinds = self.detector.kinds(cleaned)

        if kinds:
            raise SensitiveMemoryError(kinds)

        return cleaned
