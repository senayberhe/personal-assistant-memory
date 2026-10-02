class AssistantError(Exception):
    """Base class for assistant errors."""


class ConfigurationError(
    AssistantError
):
    """Configuration is invalid."""


class ValidationError(
    AssistantError
):
    """Input or arguments are invalid."""


class PermissionDeniedError(
    AssistantError
):
    """The requested action was not permitted."""


class ToolError(
    AssistantError
):
    """A tool failed during execution."""


class AgentError(
    AssistantError
):
    """The AI agent failed."""


class ServiceError(
    AssistantError
):
    """A service failed."""