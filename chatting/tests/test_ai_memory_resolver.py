import pytest

from assistant.memory.resolution.ai import (
    AIMemoryResolver,
)
from assistant.memory.resolution.types import (
    MemoryResolution,
)


def test_parse_valid_create_response():

    result = AIMemoryResolver._parse_response(
        """
        {
            "resolution": "CREATE",
            "confidence": 1.0,
            "reason": "No existing memory."
        }
        """
    )

    assert (
        result.resolution
        == MemoryResolution.CREATE
    )

    assert result.confidence == 1.0

    assert (
        result.reason
        == "No existing memory."
    )


def test_parse_contradiction_response():

    result = AIMemoryResolver._parse_response(
        """
        {
            "resolution": "CONTRADICT",
            "confidence": 0.96,
            "reason": "The statements conflict."
        }
        """
    )

    assert (
        result.resolution
        == MemoryResolution.CONTRADICT
    )

    assert result.confidence == 0.96


def test_invalid_json_is_rejected():

    with pytest.raises(ValueError):

        AIMemoryResolver._parse_response(
            "this is not json"
        )


def test_unknown_resolution_is_rejected():

    with pytest.raises(ValueError):

        AIMemoryResolver._parse_response(
            """
            {
                "resolution": "MAGIC",
                "confidence": 0.9,
                "reason": "Unknown."
            }
            """
        )


def test_confidence_above_one_is_rejected():

    with pytest.raises(ValueError):

        AIMemoryResolver._parse_response(
            """
            {
                "resolution": "UPDATE",
                "confidence": 1.5,
                "reason": "Invalid confidence."
            }
            """
        )


def test_empty_reason_is_rejected():

    with pytest.raises(ValueError):

        AIMemoryResolver._parse_response(
            """
            {
                "resolution": "UPDATE",
                "confidence": 0.8,
                "reason": ""
            }
            """
        )