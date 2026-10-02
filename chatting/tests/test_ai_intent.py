from unittest.mock import MagicMock

import pytest
from openai import OpenAIError

from assistant.errors import ServiceError
from services.ai_intent import AIIntentService, IntentResult


def make_service(result: IntentResult | None):

    client = MagicMock()

    client.responses.parse.return_value = MagicMock(
        output_parsed=result
    )

    settings = MagicMock()
    settings.model = "test-model"

    return AIIntentService(
        settings=settings,
        client=client,
    ), client


def test_open_app_intent():

    service, _ = make_service(
        IntentResult(intent="open_app", app="chrome")
    )

    result = service.detect_intent("open chrome")

    assert result.intent == "open_app"
    assert result.to_tool_call() == ("open_chrome", {})


def test_search_intent_maps_to_tool_call():

    service, client = make_service(
        IntentResult(
            intent="search_google",
            query="Python decorators",
        )
    )

    result = service.detect_intent(
        "search google for Python decorators"
    )

    assert result.to_tool_call() == (
        "search_google",
        {"query": "Python decorators"},
    )

    assert (
        client.responses.parse.call_args.kwargs["model"]
        == "test-model"
    )


def test_website_intent():

    service, _ = make_service(
        IntentResult(
            intent="open_website",
            website="github.com",
        )
    )

    result = service.detect_intent("open github.com")

    assert result.to_tool_call() == (
        "open_website",
        {"website": "github.com"},
    )


def test_unsafe_website_is_rejected():

    service, _ = make_service(
        IntentResult(
            intent="open_website",
            website="file:///etc/passwd",
        )
    )

    result = service.detect_intent("open my password file")

    assert result.intent == "unknown"


def test_intent_missing_required_field_is_unknown():

    service, _ = make_service(
        IntentResult(intent="search_youtube")
    )

    result = service.detect_intent("search youtube")

    assert result.intent == "unknown"


def test_empty_text_does_not_call_model():

    service, client = make_service(None)

    result = service.detect_intent("   ")

    assert result.intent == "unknown"
    client.responses.parse.assert_not_called()


def test_api_error_raises_service_error():

    service, client = make_service(None)

    client.responses.parse.side_effect = OpenAIError("boom")

    with pytest.raises(ServiceError):
        service.detect_intent("open chrome")
