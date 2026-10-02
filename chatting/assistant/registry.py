from dataclasses import dataclass
from typing import Callable
from assistant.security import RiskLevel


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable
    argument_model: type | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False


class ToolRegistry:

    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self.tools.get(name)

    def all(self) -> list[Tool]:
        return list(self.tools.values())