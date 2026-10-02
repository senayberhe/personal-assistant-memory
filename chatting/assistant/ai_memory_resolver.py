from openai import OpenAI
from pydantic import ValidationError

from assistant.memory_candidate import (
    MemoryCandidate,
)
from assistant.memory_model import Memory
from assistant.memory_resolution import (
    MemoryResolution,
)
from assistant.memory_resolution_result import (
    MemoryResolutionResult,
)
from assistant.memory_resolution_context import (
    MemoryResolutionContextBuilder,
)
from assistant.memory_resolution_prompt import (
    MemoryResolutionPromptBuilder,
)
from assistant.memory_resolution_schema import (
    AIMemoryResolution,
    AIResolution,
)
from config.settings import Settings


class AIMemoryResolver:
    """
    Uses an OpenAI model to classify the relationship
    between a new memory and relevant existing
    memory candidates.

    The model returns structured Pydantic output.

    The resolver never modifies memory storage.
    """

    def __init__(
        self,
        settings: Settings,
        context_builder: MemoryResolutionContextBuilder | None = None,
        prompt_builder: MemoryResolutionPromptBuilder | None = None,
        client=None,
    ):
        self.client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.api_timeout,
        )
        self.model = settings.model
        self.context_builder = (
            context_builder
            if context_builder is not None
            else MemoryResolutionContextBuilder()
        )
        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else MemoryResolutionPromptBuilder()
        )

    def resolve(
        self,
        new_content: str,
        existing_memory: Memory | None = None,
        candidates: list[MemoryCandidate] | None = None,
    ) -> MemoryResolutionResult:

        if not new_content.strip():
            raise ValueError(
                "New memory content cannot be empty."
            )

        if candidates is None:
            candidates = []

        if not candidates and existing_memory is not None:
            candidates = [
                MemoryCandidate(
                    memory=existing_memory,
                    similarity=1.0,
                    ranking_score=1.0,
                )
            ]

        if not candidates:
            return MemoryResolutionResult(
                resolution=MemoryResolution.CREATE,
                confidence=1.0,
                reason=(
                    "No relevant existing memories "
                    "were found."
                ),
            )

        # The context builder limits how many candidates
        # (and how much text) are sent to the model; the
        # prompt builder marks memory content as data,
        # not instructions.
        context = self.context_builder.build(
            candidates
        )

        response = self.client.responses.parse(
            model=self.model,
            instructions=(
                self.prompt_builder.build_instructions()
            ),
            input=self.prompt_builder.build_input(
                new_content=new_content,
                context=context,
            ),
            text_format=AIMemoryResolution,
        )

        parsed = response.output_parsed

        if parsed is None:
            raise ValueError(
                "The AI resolver did not return "
                "a structured result."
            )

        # Only candidates actually sent to the model
        # are valid targets.
        self._validate_target(
            parsed=parsed,
            candidates=context.candidates,
        )

        return parsed.to_domain_result()

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
    def _validate_target(
        parsed: AIMemoryResolution,
        candidates: list[MemoryCandidate],
    ) -> None:

        candidate_ids = {
            candidate.memory.id
            for candidate in candidates
        }

        if parsed.resolution == AIResolution.CREATE:
            if parsed.target_memory_id is not None:
                raise ValueError(
                    "CREATE resolution must not "
                    "specify a target memory."
                )
            return

        if parsed.target_memory_id is None:
            raise ValueError(
                "A target memory is required for "
                f"{parsed.resolution.value}."
            )

        if parsed.target_memory_id not in candidate_ids:
            raise ValueError(
                "AI returned a target memory ID "
                "that was not present in the "
                "candidate list."
            )
