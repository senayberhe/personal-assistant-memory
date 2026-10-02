import pytest

from assistant.safety import SensitiveDataDetector, clean_text

detector = SensitiveDataDetector()


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("my key is sk-proj-abcdefghijklmnopqrstuvwx", "openai_api_key"),
        ("AKIAIOSFODNN7EXAMPLE", "aws_access_key"),
        ("token ghp_abcdefghijklmnopqrstuvwxyz0123456789", "github_token"),
        ("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123", "bearer_token"),
        ("remember that my password is hunter2", "password"),
        ("PIN: 4821", "password"),
        ("my ssn is 123-45-6789", "us_ssn"),
        ("card 4111 1111 1111 1111 exp 09/27", "payment_card"),
        ("card 4111-1111-1111-1111", "payment_card"),
        ("stripe sk_live_abcdefghijklmnop1234", "stripe_key"),
        ("AIzaSyA1234567890abcdefghijklmnopqrstuv", "google_api_key"),
        ("xoxb-1234567890-abcdefghij", "slack_token"),
        (
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N",
            "jwt",
        ),
        ("postgres://admin:s3cret@db.example.com/app", "url_credentials"),
        ("the password for the wifi is sunflower", "password"),
        ("my passphrase: correct horse battery", "password"),
        ("my api key is abc123def456ghi", "credential"),
        ("token = 9f8e7d6c5b4a3210", "credential"),
        ("IBAN DE89 3704 0044 0532 0130 00", "bank_account"),
        ("GB82WEST12345698765432", "bank_account"),
        (
            "-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----",
            "private_key",
        ),
    ],
)
def test_detects_sensitive_data(text, kind):
    assert kind in detector.kinds(text)


@pytest.mark.parametrize(
    "text",
    [
        "I prefer Python.",
        "My favorite number is 42.",
        "Call me at 555-123-4567.",
        "I was born in 1999 and moved in 2015.",
        "The order number is 1234567890123",  # fails the Luhn check
        "I forgot my password yesterday.",  # mentions, but no value
        "Ask for the skeleton key.",
        "My token is ready.",  # too short to be a credential
        "The secret is to practice daily.",  # 'to' is not a secret
        "Visit https://example.com/page",  # URL without credentials
        "Meeting room DE12 is free.",  # not a valid IBAN
        "I like python programming",
    ],
)
def test_ordinary_text_is_not_flagged(text):
    assert not detector.contains_sensitive_data(text)


def test_redact_replaces_only_the_secret():
    text = "use sk-proj-abcdefghijklmnopqrstuvwx for the API"

    assert detector.redact(text) == "use [REDACTED] for the API"


def test_redact_handles_multiple_secrets():
    text = "password: hunter2 and card 4111 1111 1111 1111"

    redacted = detector.redact(text)

    assert "hunter2" not in redacted
    assert "4111" not in redacted
    assert redacted.count("[REDACTED]") == 2


def test_redact_without_secrets_returns_text_unchanged():
    assert detector.redact("hello") == "hello"


def test_clean_text_removes_control_characters_and_bounds_length():
    assert clean_text("  hi\x1b[31m there\x00  ", max_length=100) == "hi[31m there"
    assert clean_text("abcdef", max_length=3) == "abc"


def test_clean_text_keeps_newlines_and_tabs():
    assert clean_text("a\nb\tc", max_length=100) == "a\nb\tc"


def test_clean_text_normalizes_lookalike_characters():
    # Fullwidth letters become ASCII, so they cannot dodge detection.
    cleaned = clean_text("ｐａｓｓｗｏｒｄ is hunter2", max_length=100)

    assert detector.contains_sensitive_data(cleaned)


def test_clean_text_rejects_invalid_limit():
    with pytest.raises(ValueError):
        clean_text("x", max_length=0)
