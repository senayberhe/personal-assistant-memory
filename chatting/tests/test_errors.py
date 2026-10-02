
from assistant.errors import (
    AssistantError,
    ConfigurationError,
    ToolError,
)


def test_configuration_error_is_assistant_error():

    error = ConfigurationError(
        "Missing API key"
    )

    assert isinstance(
        error,
        AssistantError,
    )


def test_tool_error_is_assistant_error():

    error = ToolError(
        "Tool failed"
    )

    assert isinstance(
        error,
        AssistantError,
    )


def test_error_message():

    error = ToolError(
        "Search failed"
    )

    assert str(error) == (
        "Search failed"
    )