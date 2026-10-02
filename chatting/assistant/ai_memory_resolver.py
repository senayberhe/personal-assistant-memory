from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from assistant.errors import ServiceError

from assistant.memory_model import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)
from assistant.memory_resolution_schema import (
    AIMemoryResolution,
)
from config.settings import Settings


class AIMemoryResolver:
    """
    Uses an OpenAI model to classify the relationship
    between a new memory and an existing memory.

    The model returns structured data validated
    by Pydantic.

    The resolver never modifies memory storage.
    """

    def __init__(
        self,
        settings: Settings,
        client=None,
    ):
        self.client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.api_timeout,
        )

        self.model = settings.model

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None,
    ) -> MemoryResolutionResult:

        if not new_content.strip():
            raise ValueError(
                "New memory content cannot be empty."
            )

        if existing_memory is None:
            return MemoryResolutionResult(
                resolution=MemoryResolution.CREATE,
                confidence=1.0,
                reason=(
                    "No existing memory was found."
                ),
            )

        prompt = self._build_prompt(
            new_content=new_content,
            existing_memory=existing_memory,
        )

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=self._instructions(),
                input=prompt,
                text_format=AIMemoryResolution,
            )

        except OpenAIError as error:
            raise ServiceError(
                "AI memory resolution failed."
            ) from error

        parsed = response.output_parsed

        if parsed is None:
            raise ValueError(
                "The AI resolver did not return "
                "a structured result."
            )

        result = parsed.to_domain_result()

        # CREATE means "no existing memory", but there is
        # one here. Treat it as UNRELATED so the policy
        # still creates a separate memory.
        if result.resolution == MemoryResolution.CREATE:
            return MemoryResolutionResult(
                resolution=MemoryResolution.UNRELATED,
                confidence=result.confidence,
                reason=result.reason,
            )

        return result

    @staticmethod
    def _parse_response(
        raw_json: str,
    ) -> MemoryResolutionResult:
        """
        Validate a raw JSON answer from the model.

        Raises ValueError for invalid JSON, unknown
        labels, out-of-range confidence, or an empty
        reason.
        """

        try:
            parsed = AIMemoryResolution.model_validate_json(
                raw_json.strip()
            )

        except ValidationError as error:
            raise ValueError(
                f"Invalid AI memory resolution: {error}"
            ) from error

        return parsed.to_domain_result()

    @staticmethod
    def _instructions() -> str:
        return """
You are a memory relationship classifier.

Compare the existing memory with the new memory.

Classify the relationship as one of:

CREATE
IGNORE
UPDATE
CONTRADICT
UNRELATED

Definitions:

CREATE:
There is no existing memory.

IGNORE:
The new memory contains essentially the
same information as the existing memory.

UPDATE:
The new memory is related and provides a
reasonable refinement or update.

CONTRADICT:
The new memory conflicts with the existing
memory.

UNRELATED:
The new memory does not meaningfully relate
to the existing memory.

Important rules:

1. Do not invent facts.
2. Do not assume that learning something new
   contradicts an existing preference.
3. Do not assume that using two technologies
   means the user stopped using the first one.
4. Only classify CONTRADICT when the statements
   genuinely conflict.
5. Keep the reason short and factual.
6. Confidence must reflect uncertainty.
""".strip()

    @staticmethod
    def _build_prompt(
        new_content: str,
        existing_memory: Memory,
    ) -> str:

        return f"""
Existing memory:

{existing_memory.content}

New memory:

{new_content}

Determine the relationship between them.
""".strip()