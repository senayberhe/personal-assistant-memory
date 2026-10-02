import logging

from assistant.observability import (
    get_request_id,
)


class RequestIdFilter(logging.Filter):

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:

        record.request_id = (
            get_request_id()
            or "-"
        )

        return True


def configure_logging(
    environment: str,
    log_level: str,
) -> None:

    if log_level.upper() == "DEBUG":
        level = logging.DEBUG

    elif log_level.upper() == "WARNING":
        level = logging.WARNING

    elif log_level.upper() == "ERROR":
        level = logging.ERROR

    else:
        level = logging.INFO

    handler = logging.StreamHandler()

    handler.addFilter(
        RequestIdFilter()
    )

    formatter = logging.Formatter(
        "%(asctime)s "
        "%(levelname)s "
        "request_id=%(request_id)s "
        "%(name)s "
        "%(message)s"
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    root_logger.handlers.clear()

    root_logger.addHandler(handler)

    root_logger.setLevel(level)