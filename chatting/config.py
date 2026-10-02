from dataclasses import dataclass

@dataclass(frozen=True)
class AgentConfig:
    model: str = "gpt-5.6-luna"

    max_steps: int = 10
    api_timeout: float = 30.0
