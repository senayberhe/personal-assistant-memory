import logging

import openai

from assistant.memory.resolution.ai import (
    AIMemoryResolver,
)
from assistant.memory.retrieval.candidate import (
    MemoryCandidate,
)
from assistant.memory.model import Memory
from assistant.memory.resolution.result import (
    MemoryResolutionResult,
)
from assistant.memory.resolution.rules import (
    MemoryResolver,
)


logger = logging.getLogger(__name__)


class ResilientMemoryResolver:
    """
    Attempts AI-based memory resolution first.

    Falls back to the rule-based resolver when
    the AI service experiences a transient failure.
    """

    def __init__(
        self,
        ai_resolver: AIMemoryResolver,
        fallback_resolver: MemoryResolver,
    ):
        self.ai_resolver = ai_resolver
        self.fallback_resolver = fallback_resolver

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None = None,
        candidates: list[MemoryCandidate] | None = None,
    ) -> MemoryResolutionResult:

        try:
            logger.debug(
                "Attempting AI memory resolution."
            )

            return self.ai_resolver.resolve(
                new_content=new_content,
                existing_memory=existing_memory,
                candidates=candidates,
            )

        except (
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.RateLimitError,
        ) as error:

            logger.warning(
                "AI memory resolver temporarily "
                "unavailable. Falling back to "
                "rule-based resolver. error=%s",
                type(error).__name__,
            )

            return self.fallback_resolver.resolve(
                new_content=new_content,
                existing_memory=existing_memory,
                candidates=candidates,
            )

        except ValueError as error:

            # The AI answered, but the answer was invalid
            # (for example an unknown target_memory_id).
            # Empty content is re-checked by the fallback,
            # which raises the same ValueError.
            logger.warning(
                "AI memory resolver returned an invalid "
                "result. Falling back to rule-based "
                "resolver. error=%s",
                error,
            )

            return self.fallback_resolver.resolve(
                new_content=new_content,
                existing_memory=existing_memory,
                candidates=candidates,
            )