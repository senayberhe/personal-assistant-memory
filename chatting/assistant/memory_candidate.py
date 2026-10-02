from dataclasses import dataclass

from assistant.memory_model import Memory


@dataclass(frozen=True)
class MemoryCandidate:
    """
    Represents a memory that may be relevant to
    a new memory being evaluated.

    The candidate contains:

    - the memory itself
    - semantic similarity
    - final ranking score
    """

    memory: Memory
    similarity: float
    ranking_score: float