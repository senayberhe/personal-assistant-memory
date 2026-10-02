import logging
import uuid
from contextvars import ContextVar
from contextlib import contextmanager
from time import perf_counter


request_id_context: ContextVar[str|None] = ContextVar("request_id_context", default=None)


def create_request_id() -> str:
    return uuid.uuid4().hex[:12]

def set_request_id(request_id: str) -> None:
    request_id_context.set(request_id)


def get_request_id() -> str | None:
    return request_id_context.get()

def clear_request_id() -> None:
    request_id_context.set(None)

@contextmanager
def request_context():
    request_id = create_request_id()

    token = request_id_context.set(request_id)
    try:
        yield request_id
    finally:
        request_id_context.reset(token)


@contextmanager
def measure_time(operation: str):
    start = perf_counter()
    try:
        yield
    finally:
        elapsed = (perf_counter() - start)
        logger = logging.getLogger("assistant.performance")
        logger.info(
            "operation=%s operation_latency_seconds=%.4f",
            operation,
            elapsed,
        )