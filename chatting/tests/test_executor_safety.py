import time
from unittest.mock import MagicMock

import pytest

from assistant.errors import PermissionDeniedError, ToolError
from assistant.tools.executor import ToolExecutor
from assistant.tools.permissions import PermissionManager
from assistant.tools.rate_limit import RateLimiter
from assistant.tools.registry import Tool, ToolRegistry
from assistant.tools.security import RiskLevel, SecurityPolicy


def make_executor(handler=lambda: "ok", **kwargs):
    registry = ToolRegistry()
    registry.register(Tool(name="tool", description="test", handler=handler))

    permissions = MagicMock()
    permissions.confirm.return_value = True

    return ToolExecutor(registry=registry, permission_manager=permissions, **kwargs)


def test_slow_tool_times_out():
    executor = make_executor(
        handler=lambda: time.sleep(2) or "late",
        timeout_seconds=0.1,
    )

    started = time.perf_counter()

    with pytest.raises(ToolError, match="timed out"):
        executor.execute("tool", {})

    assert time.perf_counter() - started < 1
    assert executor.metrics.get("tool").failures == 1

    executor.shutdown()


def test_rate_limit_blocks_rapid_calls():
    executor = make_executor(
        rate_limiter=RateLimiter(max_calls=2, window_seconds=60)
    )

    executor.execute("tool", {})
    executor.execute("tool", {})

    with pytest.raises(ToolError, match="Too many actions"):
        executor.execute("tool", {})


def test_oversized_arguments_are_rejected():
    executor = make_executor(max_argument_characters=50)

    with pytest.raises(ToolError, match="too large"):
        executor.execute("tool", {"query": "x" * 100})


def test_non_object_arguments_are_rejected():
    executor = make_executor()

    with pytest.raises(ToolError, match="must be an object"):
        executor.execute("tool", ["not", "a", "dict"])


def test_long_results_are_truncated():
    executor = make_executor(
        handler=lambda: "y" * 100,
        max_result_characters=10,
    )

    assert executor.execute("tool", {}) == "y" * 10 + " [truncated]"


def test_metrics_record_successes():
    executor = make_executor()

    executor.execute("tool", {})

    metrics = executor.metrics.get("tool")

    assert (metrics.calls, metrics.successes) == (1, 1)


def test_permission_manager_uses_injected_confirm():
    questions = []

    def deny(question: str) -> bool:
        questions.append(question)
        return False

    manager = PermissionManager(SecurityPolicy(), confirm=deny)

    risky = Tool(
        name="open_terminal",
        description="",
        handler=lambda: None,
        risk_level=RiskLevel.HIGH,
    )

    assert manager.confirm(risky) is False
    assert "high risk" in questions[0]


def test_critical_tools_are_blocked_without_asking():
    manager = PermissionManager(
        SecurityPolicy(),
        confirm=lambda question: pytest.fail("must not ask"),
    )

    critical = Tool(
        name="wipe",
        description="",
        handler=lambda: None,
        risk_level=RiskLevel.CRITICAL,
    )

    assert manager.confirm(critical) is False


def test_denied_permission_raises():
    registry = ToolRegistry()
    registry.register(Tool(name="tool", description="", handler=lambda: "ok"))

    permissions = MagicMock()
    permissions.confirm.return_value = False

    executor = ToolExecutor(registry=registry, permission_manager=permissions)

    with pytest.raises(PermissionDeniedError):
        executor.execute("tool", {})
