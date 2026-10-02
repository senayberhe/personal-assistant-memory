from dataclasses import dataclass, field


@dataclass
class AgentState:
    current_task: str | None = None

    variables: dict = field(
        default_factory = dict
    )

    is_running: bool = False
