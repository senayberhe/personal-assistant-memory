from datetime import datetime
from unittest.mock import MagicMock

import openai

from assistant.memory.model import Memory
from assistant.memory.resolution.resilient import (
    ResilientMemoryResolver,
)
from assistant.memory.resolution.result import (
    MemoryResolutionResult,
)
from assistant.memory.resolution.types import (
    MemoryResolution,
)


def create_memory():
    return Memory(
        id="memory-1",
        content="I prefer Python.",
        created_at=datetime.now(),
    )


def create_result():
    return MemoryResolutionResult(
        resolution=MemoryResolution.CONTRADICT,
        confidence=0.95,
        reason="The preferences conflict.",
    )


def test_ai_result_is_returned_when_ai_succeeds():

    ai_resolver = MagicMock()

    fallback_resolver = MagicMock()

    expected_result = create_result()

    ai_resolver.resolve.return_value = (
        expected_result
    )

    resolver = ResilientMemoryResolver(
        ai_resolver=ai_resolver,
        fallback_resolver=fallback_resolver,
    )

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=create_memory(),
    )

    assert result is expected_result

    ai_resolver.resolve.assert_called_once()

    fallback_resolver.resolve.assert_not_called()


def test_timeout_uses_fallback():

    ai_resolver = MagicMock()

    fallback_resolver = MagicMock()

    fallback_result = (
        create_result()
    )

    ai_resolver.resolve.side_effect = (
        openai.APITimeoutError(
            request=MagicMock()
        )
    )

    fallback_resolver.resolve.return_value = (
        fallback_result
    )

    resolver = ResilientMemoryResolver(
        ai_resolver=ai_resolver,
        fallback_resolver=fallback_resolver,
    )

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=create_memory(),
    )

    assert result is fallback_result

    ai_resolver.resolve.assert_called_once()

    fallback_resolver.resolve.assert_called_once()


def test_connection_error_uses_fallback():

    ai_resolver = MagicMock()

    fallback_resolver = MagicMock()

    fallback_result = create_result()

    ai_resolver.resolve.side_effect = (
        openai.APIConnectionError(
            request=MagicMock()
        )
    )

    fallback_resolver.resolve.return_value = (
        fallback_result
    )

    resolver = ResilientMemoryResolver(
        ai_resolver=ai_resolver,
        fallback_resolver=fallback_resolver,
    )

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=create_memory(),
    )

    assert result is fallback_result

    fallback_resolver.resolve.assert_called_once()


def test_rate_limit_uses_fallback():

    ai_resolver = MagicMock()

    fallback_resolver = MagicMock()

    fallback_result = create_result()

    response = MagicMock()
    response.status_code = 429
    response.request = MagicMock()

    ai_resolver.resolve.side_effect = (
        openai.RateLimitError(
            "Rate limit",
            response=response,
            body=None,
        )
    )

    fallback_resolver.resolve.return_value = (
        fallback_result
    )

    resolver = ResilientMemoryResolver(
        ai_resolver=ai_resolver,
        fallback_resolver=fallback_resolver,
    )

    result = resolver.resolve(
        new_content="I don't prefer Python.",
        existing_memory=create_memory(),
    )

    assert result is fallback_result

    fallback_resolver.resolve.assert_called_once()