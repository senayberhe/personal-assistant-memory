import pytest

from assistant.errors import ConfigurationError
from config.settings import Settings


def test_settings_are_created():

    settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        environment="testing",
        log_level="WARNING",
        api_timeout=30,
        tool_timeout=10,
        max_agent_steps=10,
        max_plan_steps=10,
        speech_timeout=5,
        phrase_time_limit=8,
        ambient_noise_duration=1,
    )

    settings.validate()

    assert settings.model == "test-model"
    assert settings.api_timeout == 30
    assert settings.max_agent_steps == 10
    assert settings.max_plan_steps == 10
    assert settings.speech_timeout == 5
    assert settings.phrase_time_limit == 8
    assert settings.ambient_noise_duration == 1
    assert settings.openai_api_key == "test-key"
    assert settings.environment == "testing"
    assert settings.log_level == "WARNING"
    assert settings.tool_timeout == 10


def test_invalid_api_timeout():
    settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        environment="testing",
        log_level="WARNING",
        api_timeout=-1,
        tool_timeout=10,
        max_agent_steps=10,
        max_plan_steps=10,
        speech_timeout=5,
        phrase_time_limit=8,
        ambient_noise_duration=1,
    )

    with pytest.raises(ConfigurationError):
        settings.validate()