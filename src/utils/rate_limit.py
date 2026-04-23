"""
Simple token-bucket rate limiter.

Two buckets per process:

    * ALL tools:        `MCP_RATE_ALL`     (requests/sec, default 10)
    * DESTRUCTIVE only: `MCP_RATE_DESTRUCTIVE` (requests/sec, default 0.5 — one every 2s)

Both buckets have a burst capacity equal to their fill rate (minimum 1).
When a bucket is empty, the call is rejected with a human-readable
message *instead of* executing. This is deliberate: a blocking wait
would mask the LLM's bad behavior (runaway loop, accidental recursion)
instead of surfacing it.

Disable entirely by setting ``MCP_RATE_DISABLED=1``.
"""

from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger("davinci-resolve-mcp.rate_limit")


class TokenBucket:
    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self.rate = max(rate, 0.0)
        self.capacity = capacity if capacity is not None else max(self.rate, 1.0)
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def try_take(self, n: float = 1.0) -> bool:
        """Return True and consume n tokens; False if not enough."""
        if self.rate <= 0:
            return True  # disabled bucket
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def snapshot(self) -> dict:
        return {
            "rate": self.rate,
            "capacity": self.capacity,
            "tokens": round(self._tokens, 3),
        }


class RateLimiter:
    def __init__(self) -> None:
        disabled = os.environ.get("MCP_RATE_DISABLED") == "1"
        rate_all = float(os.environ.get("MCP_RATE_ALL", "10"))
        rate_destr = float(os.environ.get("MCP_RATE_DESTRUCTIVE", "0.5"))
        if disabled:
            rate_all = 0
            rate_destr = 0
        self.all = TokenBucket(rate_all)
        self.destructive = TokenBucket(rate_destr)

    def check(self, *, destructive: bool) -> tuple[bool, str | None]:
        """Return (allowed, reason-if-rejected)."""
        if destructive and not self.destructive.try_take():
            return False, (
                "rate limited: destructive-tool budget exhausted "
                f"(max {self.destructive.rate}/s)"
            )
        if not self.all.try_take():
            return False, (
                "rate limited: global tool budget exhausted "
                f"(max {self.all.rate}/s)"
            )
        return True, None

    def snapshot(self) -> dict:
        return {
            "all": self.all.snapshot(),
            "destructive": self.destructive.snapshot(),
        }


# Module-level singleton, built once per process from env.
rate_limiter = RateLimiter()
