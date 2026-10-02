import logging
from typing import Literal

from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from assistant.errors import ServiceError
from config.settings import Settings
from services.url_security import validate_url

logger = logging.getLogger(__name__)


INSTRUCTIONS = (
    "Classify the user's voice command for a macOS assistant.\n"
    "- open_app: the user wants to open chrome, safari or terminal. "
    "Set app.\n"
    "- open_website: the user names a website or URL. "
    "Set website to the domain or URL.\n"
    "- search_google / search_youtube: set query to the search terms "
    "only, without words like 'search google for'.\n"
    "- unknown: anything else, including unsupported apps and any "
    "destructive or risky request.\n"
    "Set every field that does not apply to null."
)


class IntentResult(BaseModel):
    intent: Literal[
        "open_app",
        "open_website",
        "search_google",
        "search_youtube",
        "unknown",
    ]
    app: Literal["chrome", "safari", "terminal"] | None = None
    website: str | None = None
    query: str | None = None

    def to_tool_call(self) -> tuple[str, dict] | None:
        """Return the (tool_name, arguments) pair for ToolExecutor."""

        if self.intent == "open_app" and self.app:
            return f"open_{self.app}", {}

        if self.intent == "open_website" and self.website:
            return "open_website", {"website": self.website}

        if self.intent in {"search_google", "search_youtube"} and self.query:
            return self.intent, {"query": self.query}

        return None


UNKNOWN = IntentResult(intent="unknown")


class AIIntentService:
    """Uses the language model to turn a spoken command into an intent."""

    def __init__(
        self,
        settings: Settings | None = None,
        client=None,
    ):
        if client is None or settings is None:
            settings = settings or Settings.from_environment()

        self.model = settings.model

        self.client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.api_timeout,
        )

    def detect_intent(
        self,
        text: str,
    ) -> IntentResult:

        if not text.strip():
            return UNKNOWN

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=INSTRUCTIONS,
                input=text,
                text_format=IntentResult,
            )

        except OpenAIError as error:
            raise ServiceError(
                "Intent detection failed."
            ) from error

        result = response.output_parsed

        if result is None:
            return UNKNOWN

        return self._validate(result)

    @staticmethod
    def _validate(
        result: IntentResult,
    ) -> IntentResult:

        if result.intent == "open_website":

            website = (result.website or "").strip()

            if "://" not in website:
                website = f"https://{website}"

            try:
                validate_url(website)

            except ValueError:
                logger.info(
                    "Rejected website from intent: %r",
                    result.website,
                )
                return UNKNOWN

        if result.to_tool_call() is None:
            return UNKNOWN

        return result


if __name__ == "__main__":

    service = AIIntentService()

    for command in [
        "open chrome",
        "search google for Python decorators",
        "open github.com",
        "open unknown app",
        "open the terminal",
        "delete everything on my computer",
    ]:
        print(f"\nUser: {command}")
        print(f"Intent: {service.detect_intent(command)}")
