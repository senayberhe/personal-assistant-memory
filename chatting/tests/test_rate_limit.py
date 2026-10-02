from assistant.tools.rate_limit import (
    RateLimiter,
)


def test_rate_limit():
    limiter = RateLimiter(max_calls=2, window_seconds=1)

    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False
    assert not limiter.allow()