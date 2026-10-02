from unittest.mock import MagicMock

import pytest

from assistant.errors import ToolError

from assistant.tools.executor import (
    ToolExecutor,
)
from assistant.tools.registry import (
    Tool,
    ToolRegistry,
)


def test_executor_runs_tool():

    registry = ToolRegistry()

    tool = Tool(
        name="hello",
        description="Say hello",
        handler=lambda: "Hello!",
    )

    registry.register(tool)

    permissions = MagicMock()

    permissions.confirm.return_value = True

    executor = ToolExecutor(
        registry=registry,
        permission_manager=permissions,
    )

    result = executor.execute(
        "hello",
        {},
    )

    assert result == "Hello!"


def test_executor_rejects_unknown_tool():

    registry = ToolRegistry()

    permissions = MagicMock()

    executor = ToolExecutor(
        registry=registry,
        permission_manager=permissions,
    )

    with pytest.raises(ToolError):

        executor.execute(
            "unknown",
            {},
        )
