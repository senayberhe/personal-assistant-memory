import pytest

from services.url_security import (
    validate_url,
)


def test_https_url_is_allowed():

    result = validate_url(
        "https://example.com"
    )

    assert result == (
        "https://example.com"
    )


def test_http_url_is_allowed():

    result = validate_url(
        "http://example.com"
    )

    assert result == (
        "http://example.com"
    )


def test_file_url_is_rejected():

    with pytest.raises(ValueError):

        validate_url(
            "file:///etc/passwd"
        )


def test_empty_url_is_rejected():

    with pytest.raises(ValueError):

        validate_url("")