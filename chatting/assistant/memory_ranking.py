from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from assistant.memory_model import Memory
    from assistant.retrieval import RetrievedMemory


SIMILARITY_WEIGHT = 0.60
IMPORTANCE_WEIGHT = 0.25
RECENCY_WEIGHT = 0.15


@dataclass
class RankedMemory:
    memory: Memory
    similarity: float
    importance: float
    recency: float
    final_score: float


def calculate_recency(
    created_at: datetime,
    now: datetime | None = None,
    decay_days: float = 30.0,
) -> float:

    if now is None:
        now = datetime.now(
            created_at.tzinfo
        )

    age_seconds = (
        now - created_at
    ).total_seconds()

    age_days = max(
        0.0,
        age_seconds / 86400,
    )

    return math.exp(
        -age_days / decay_days
    )


def calculate_final_score(
    similarity: float,
    importance: float,
    recency: float,
) -> float:

    return (
        SIMILARITY_WEIGHT * similarity
        + IMPORTANCE_WEIGHT * importance
        + RECENCY_WEIGHT * recency
    )


def rank_memories(
    results: list[RetrievedMemory],
    now: datetime | None = None,
) -> list[RankedMemory]:

    ranked = []

    for result in results:

        memory = result.memory

        recency = calculate_recency(
            memory.created_at,
            now=now,
        )

        ranked.append(
            RankedMemory(
                memory=memory,
                similarity=result.score,
                importance=memory.importance,
                recency=recency,
                final_score=calculate_final_score(
                    similarity=result.score,
                    importance=memory.importance,
                    recency=recency,
                ),
            )
        )

    ranked.sort(
        key=lambda item: item.final_score,
        reverse=True,
    )

    return ranked
