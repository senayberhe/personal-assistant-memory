import logging

from config.logging_config import RedactingFormatter, configure_logging


def make_record(message, *args, exc_info=None):
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=args,
        exc_info=exc_info,
    )


def test_secrets_in_messages_are_redacted():
    formatter = RedactingFormatter("%(message)s")

    record = make_record("You: my key is %s", "sk-proj-abcdefghijklmnopqrstuvwx")

    assert formatter.format(record) == "You: my key is [REDACTED]"


def test_secrets_in_tracebacks_are_redacted():
    formatter = RedactingFormatter("%(message)s")

    try:
        raise ValueError("password: hunter2")
    except ValueError:
        import sys

        record = make_record("failed", exc_info=sys.exc_info())

    output = formatter.format(record)

    assert "hunter2" not in output
    assert "ValueError" in output


def test_log_file_receives_redacted_logs(tmp_path):
    log_file = tmp_path / "logs" / "assistant.log"

    configure_logging(
        environment="testing",
        log_level="INFO",
        log_file=log_file,
        console_level="ERROR",
    )

    logging.getLogger("test").info("token %s", "sk-proj-abcdefghijklmnopqrstuvwx")

    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_file.read_text()

    assert "[REDACTED]" in content
    assert "sk-proj" not in content

    # Restore pytest's default logging setup for other tests.
    logging.getLogger().handlers.clear()
