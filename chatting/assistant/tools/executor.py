"""
ToolExecutor: runs a tool the model asked for, safely.

Every call goes through the same checks, in order:

1. the tool exists
2. the rate limit is not exceeded
3. the arguments are a reasonably sized JSON object
4. the user/policy allows it (PermissionManager)
5. the arguments match the tool's schema (Pydantic)
6. the tool finishes within the timeout
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from time import perf_counter

from assistant.errors import PermissionDeniedError, ToolError
from assistant.tools.metrics import Metrics
from assistant.tools.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

DEFAULT_MAX_ARGUMENT_CHARACTERS = 2_000
DEFAULT_MAX_RESULT_CHARACTERS = 4_000


class ToolExecutor:

    def __init__(
        self,
        registry,
        permission_manager,
        timeout_seconds: float | None = None,
        rate_limiter: RateLimiter | None = None,
        metrics: Metrics | None = None,
        max_argument_characters: int = DEFAULT_MAX_ARGUMENT_CHARACTERS,
        max_result_characters: int = DEFAULT_MAX_RESULT_CHARACTERS,
    ):
        """
        timeout_seconds:
            Maximum run time per tool call; None means no limit.
        rate_limiter:
            Limits how many tool calls can run in a time window,
            so a looping model cannot spam actions.
        metrics:
            Records calls, failures and latency per tool.
        """

        self.registry = registry
        self.permission_manager = permission_manager
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = rate_limiter
        self.metrics = metrics if metrics is not None else Metrics()
        self.max_argument_characters = max_argument_characters
        self.max_result_characters = max_result_characters

        # Shared worker pool for timeouts. A timed-out tool keeps
        # running in its thread (Python cannot kill threads), but
        # the assistant stops waiting for it.
        self._pool = (
            ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix="tool",
            )
            if timeout_seconds is not None
            else None
        )

    def execute(
        self,
        tool_name: str,
        arguments: dict,
    ) -> str:

        tool = self.registry.get(tool_name)

        if tool is None:
            raise ToolError(f"Unknown tool: {tool_name}")

        if self.rate_limiter is not None and not self.rate_limiter.allow():
            logger.warning("Tool rate limit reached: %s", tool_name)

            raise ToolError(
                "Too many actions in a short time. Please wait a moment."
            )

        self._check_argument_shape(tool_name, arguments)

        try:
            allowed = self.permission_manager.confirm(tool)

        except Exception as error:
            raise PermissionDeniedError("Permission check failed.") from error

        if not allowed:
            logger.info("Tool denied: %s", tool_name)

            raise PermissionDeniedError(
                f"Permission denied for '{tool_name}'."
            )

        validated_arguments = arguments

        if tool.argument_model is not None:
            try:
                validated_arguments = tool.argument_model(
                    **arguments
                ).model_dump()

            except Exception as error:
                raise ToolError(
                    f"Invalid arguments for '{tool_name}'."
                ) from error

        return self._run(tool, validated_arguments)

    def _check_argument_shape(
        self,
        tool_name: str,
        arguments: dict,
    ) -> None:

        if not isinstance(arguments, dict):
            raise ToolError(
                f"Arguments for '{tool_name}' must be an object."
            )

        size = len(json.dumps(arguments, default=str))

        if size > self.max_argument_characters:
            raise ToolError(f"Arguments for '{tool_name}' are too large.")

    def _run(
        self,
        tool,
        arguments: dict,
    ) -> str:

        logger.info("Executing tool=%s", tool.name)

        started = perf_counter()

        try:
            if self._pool is None:
                result = tool.handler(**arguments)

            else:
                future = self._pool.submit(tool.handler, **arguments)
                result = future.result(timeout=self.timeout_seconds)

        except FutureTimeoutError as error:
            self.metrics.record_failure(tool.name, perf_counter() - started)

            logger.error(
                "Tool timed out=%s after %.1fs",
                tool.name,
                self.timeout_seconds,
            )

            raise ToolError(f"Tool '{tool.name}' timed out.") from error

        except Exception as error:
            self.metrics.record_failure(tool.name, perf_counter() - started)

            logger.exception("Tool execution failed=%s", tool.name)

            raise ToolError(f"Tool '{tool.name}' failed.") from error

        self.metrics.record_success(tool.name, perf_counter() - started)

        logger.info("Tool completed=%s", tool.name)

        output = str(result)

        if len(output) > self.max_result_characters:
            output = output[: self.max_result_characters] + " [truncated]"

        return output

    def shutdown(self) -> None:
        """Stop the worker pool (does not wait for stuck tools)."""

        if self._pool is not None:
            self._pool.shutdown(wait=False, cancel_futures=True)
