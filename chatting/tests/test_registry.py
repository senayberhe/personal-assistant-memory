from assistant.tools.registry import (
    Tool,
    ToolRegistry,
)


def test_register_and_get_tool():

    registry = ToolRegistry()

    tool = Tool(
        name="test_tool",
        description="Test tool",
        handler=lambda: "hello",
    )

    registry.register(tool)

    result = registry.get(
        "test_tool"
    )

    assert result is tool


def test_unknown_tool_returns_none():

    registry = ToolRegistry()

    result = registry.get(
        "does_not_exist"
    )

    assert result is None