import pytest

from assistant.memory import validate_importance


def test_valid_importance():
    assert validate_importance(0.0) == 0.0
    assert validate_importance(0.5) == 0.5
    assert validate_importance(1.0) == 1.0

def test_negative_importance_fails():
    with pytest.raises(ValueError):
        validate_importance(-0.1)

def test_importance_greater_than_one_fails():
    with pytest.raises(ValueError):
        validate_importance(1.1)