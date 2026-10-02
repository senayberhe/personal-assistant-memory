from dataclasses import dataclass

from assistant.memory_candidate import MemoryCandidate


@dataclass(frozen=True)
class ResolutionContext:
    """
    Compact context sent to the AI memory resolver.
    """

    candidates: list[MemoryCandidate]
    text: str


class MemoryResolutionContextBuilder:
    """
    Builds a compact representation of memory candidates.

    The builder protects the AI context from becoming
    unnecessarily large.
    """

    def __init__(
        self,
        max_candidates: int = 5,
        max_characters: int = 6000,
        max_content_characters: int = 1000,
    ):
        if max_candidates <= 0:
            raise ValueError(
                "max_candidates must be greater than zero."
            )

        if max_characters <= 0:
            raise ValueError(
                "max_characters must be greater than zero."
            )

        if max_content_characters <= 0:
            raise ValueError(
                "max_content_characters must be greater than zero."
            )

        self.max_candidates = max_candidates
        self.max_characters = max_characters
        self.max_content_characters = (
            max_content_characters
        )

    def build(
        self,
        candidates: list[MemoryCandidate],
    ) -> ResolutionContext:

        selected = candidates[
            : self.max_candidates
        ]

        lines: list[str] = []

        for index, candidate in enumerate(
            selected,
            start=1,
        ):
            content = self._truncate_content(
                candidate.memory.content
            )

            line = (
                f"Candidate {index}\n"
                f"Memory ID: {candidate.memory.id}\n"
                f"Memory type: "
                f"{candidate.memory.memory_type}\n"
                f"Similarity: "
                f"{candidate.similarity:.4f}\n"
                f"Ranking score: "
                f"{candidate.ranking_score:.4f}\n"
                f"Content: {content}"
            )

            lines.append(line)

        text = "\n\n".join(lines)

        if len(text) > self.max_characters:
            text = text[
                : self.max_characters
            ]

            text += (
                "\n\n[Candidate context truncated.]"
            )

        return ResolutionContext(
            candidates=selected,
            text=text,
        )

    def _truncate_content(
        self,
        content: str,
    ) -> str:

        content = content.strip()

        if len(content) <= self.max_content_characters:
            return content

        return (
            content[
                : self.max_content_characters
            ]
            + "..."
        )