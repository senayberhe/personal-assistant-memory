import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from assistant.observability import get_request_id
from assistant.safety import SensitiveDataDetector

LOG_FORMAT = (
    "%(asctime)s %(levelname)s request_id=%(request_id)s %(name)s %(message)s"
)

# Chatty third-party libraries: only show their warnings.
NOISY_LOGGERS = ("chromadb", "httpx", "httpcore", "openai", "urllib3")


class RequestIdFilter(logging.Filter):
    """Adds the current request ID to every record."""

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:

        record.request_id = get_request_id() or "-"

        return True


class RedactingFormatter(logging.Formatter):
    """
    Removes secrets from the final log line.

    Redacting the formatted output (instead of only the message)
    also covers arguments and exception tracebacks.
    """

    def __init__(
        self,
        fmt: str,
        detector: SensitiveDataDetector | None = None,
    ):
        super().__init__(fmt)
        self.detector = detector or SensitiveDataDetector()

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        return self.detector.redact(super().format(record))


def _parse_level(log_level: str) -> int:
    level = logging.getLevelName(log_level.upper())

    return level if isinstance(level, int) else logging.INFO


def configure_logging(
    environment: str,
    log_level: str,
    log_file: str | Path | None = None,
    console_level: str | None = None,
) -> None:
    """
    Configure root logging.

    log_file:
        Also write logs to this file (rotated at 1 MB, 3 backups).
    console_level:
        Separate level for the terminal, e.g. "WARNING" in the text
        chat UI so log lines do not interrupt the conversation.
    """

    level = _parse_level(log_level)
    formatter = RedactingFormatter(LOG_FORMAT)

    handlers: list[logging.Handler] = []

    console = logging.StreamHandler()
    console.setLevel(
        _parse_level(console_level) if console_level else level
    )
    handlers.append(console)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    for handler in handlers:
        handler.addFilter(RequestIdFilter())
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(
            max(level, logging.WARNING)
        )

    logging.getLogger(__name__).debug(
        "Logging configured (environment=%s).",
        environment,
    )
