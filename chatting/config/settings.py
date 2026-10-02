import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from assistant.errors import ConfigurationError

# chatting/: relative paths (memory, logs) are resolved against this
# folder, so the app behaves the same from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def parse_bool(value: str) -> bool:
    """Parse a true/false environment value."""

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"Not a boolean: {value!r}")


def resolve_project_path(path: str) -> str:
    """Make a relative path absolute, relative to PROJECT_ROOT."""

    candidate = Path(path).expanduser()

    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    return str(candidate)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model: str

    environment: str
    log_level: str

    api_timeout: float
    tool_timeout: float

    max_agent_steps: int
    max_plan_steps: int

    speech_timeout: int
    phrase_time_limit: int
    ambient_noise_duration: int

    embedding_model: str = "text-embedding-3-small"

    memory_directory: str = "data/memory"

    # Safety first: ask before any automatically detected fact
    # is written to long-term memory.
    memory_require_approval: bool = True

    def validate(self) -> None:
        if not self.openai_api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is not configured."
            )

        if not self.model:
            raise ConfigurationError(
                "ASSISTANT_MODEL cannot be empty."
            )

        if self.api_timeout <= 0:
            raise ConfigurationError(
                "API_TIMEOUT must be greater than zero."
            )

        if self.tool_timeout <= 0:
            raise ConfigurationError(
                "TOOL_TIMEOUT must be greater than zero."
            )

        if self.max_agent_steps <= 0:
            raise ConfigurationError(
                "MAX_AGENT_STEPS must be greater than zero."
            )

        if self.max_plan_steps <= 0:
            raise ConfigurationError(
                "MAX_PLAN_STEPS must be greater than zero."
            )

        if self.speech_timeout <= 0:
            raise ConfigurationError(
                "SPEECH_TIMEOUT must be greater than zero."
            )

        if self.phrase_time_limit <= 0:
            raise ConfigurationError(
                "PHRASE_TIME_LIMIT must be greater than zero."
            )

        if self.ambient_noise_duration < 0:
            raise ConfigurationError(
                "AMBIENT_NOISE_DURATION cannot be negative."
            )

    @classmethod
    def from_environment(cls) -> "Settings":
        try:
            settings = cls(
                openai_api_key=os.getenv(
                    "OPENAI_API_KEY",
                    "",
                ),
                model=os.getenv(
                    "ASSISTANT_MODEL",
                    "gpt-5.6-luna",
                ),
                environment=os.getenv(
                    "ENVIRONMENT",
                    "development",
                ),
                log_level=os.getenv(
                    "LOG_LEVEL",
                    "INFO",
                ),
                api_timeout=float(
                    os.getenv(
                        "API_TIMEOUT",
                        "30",
                    )
                ),
                tool_timeout=float(
                    os.getenv(
                        "TOOL_TIMEOUT",
                        "10",
                    )
                ),
                max_agent_steps=int(
                    os.getenv(
                        "MAX_AGENT_STEPS",
                        "10",
                    )
                ),
                max_plan_steps=int(
                    os.getenv(
                        "MAX_PLAN_STEPS",
                        "10",
                    )
                ),
                speech_timeout=int(
                    os.getenv(
                        "SPEECH_TIMEOUT",
                        "5",
                    )
                ),
                phrase_time_limit=int(
                    os.getenv(
                        "PHRASE_TIME_LIMIT",
                        "8",
                    )
                ),
                ambient_noise_duration=int(
                    os.getenv(
                        "AMBIENT_NOISE_DURATION",
                        "1",
                    )
                ),
                embedding_model=os.getenv(
                    "EMBEDDING_MODEL",
                    "text-embedding-3-small",
                ),
                memory_directory=resolve_project_path(
                    os.getenv(
                        "MEMORY_DIRECTORY",
                        "data/memory",
                    )
                ),
                memory_require_approval=parse_bool(
                    os.getenv(
                        "MEMORY_REQUIRE_APPROVAL",
                        "true",
                    )
                ),
            )

        except ValueError as error:
            raise ConfigurationError(
                "One or more environment variables "
                "have invalid values."
            ) from error

        settings.validate()

        return settings
