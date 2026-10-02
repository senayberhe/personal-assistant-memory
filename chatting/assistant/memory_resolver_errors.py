class MemoryResolverError(Exception):
    """
    Base exception for memory resolver failures.
    """


class MemoryResolverTransientError(
    MemoryResolverError
):
    """
    A temporary resolver failure.

    Examples:
    - timeout
    - network failure
    - rate limit
    - temporary server error
    """


class MemoryResolverPermanentError(
    MemoryResolverError
):
    """
    A non-transient resolver failure.

    Examples:
    - invalid configuration
    - authentication failure
    - invalid request
    """