"""Shared pytest fixtures."""

import pytest

from config.settings import Settings


def build_settings(**overrides) -> Settings:
    """Settings with safe test values; override any field by keyword."""

    values: dict = {
        "openai_api_key": "test-key",
        "model": "test-model",
        "environment": "testing",
        "log_level": "WARNING",
        "api_timeout": 30,
        "tool_timeout": 10,
        "max_agent_steps": 10,
        "max_plan_steps": 10,
        "speech_timeout": 5,
        "phrase_time_limit": 8,
        "ambient_noise_duration": 1,
    }

    values.update(overrides)

    return Settings(**values)


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Test settings that keep memory data inside tmp_path."""

    return build_settings(memory_directory=str(tmp_path))
