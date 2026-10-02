from assistant.observability import (
    get_request_id,
    request_context,
)


def test_request_context_creates_id():

    assert get_request_id() is None

    with request_context() as request_id:

        assert request_id
        assert (
            get_request_id()
            == request_id
        )

    assert get_request_id() is None