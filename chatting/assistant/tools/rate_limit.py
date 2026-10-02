from time import monotonic


class RateLimiter:
    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = (window_seconds)
        self.call: list[float] = []


    def allow(self) -> bool:
        now = monotonic()

        cutoff = ( now - self.window_seconds)
        self.call = [timestamp for timestamp in self.call if timestamp >= cutoff]

        if len(self.call) >= self.max_calls:
            return False
        self.call.append(now)
        return True