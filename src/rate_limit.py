"""tiny token-bucket rate limiter for outbound API calls."""
from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, rate_per_minute: int = 60, capacity: int | None = None):
        self.rate = rate_per_minute / 60.0  # tokens/sec
        self.capacity = capacity or rate_per_minute
        self._tokens = float(self.capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, n: int = 1, block: bool = True) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= n:
                self._tokens -= n
                return True
            if not block:
                return False
            need = n - self._tokens
            wait = need / self.rate
        time.sleep(wait)
        with self._lock:
            self._refill()
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def _refill(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        self._tokens = min(self.capacity, self._tokens + delta * self.rate)
        self._last = now
