"""Simple in-memory sliding-window rate limiter for the dashboard API."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """
    Sliding-window rate limiter keyed by (ip, endpoint_group).

    Default: 10 requests per 60 seconds per IP per group.
    Job creation endpoints use a tighter limit (5 per 60s) to prevent run storms.
    """

    def __init__(self, window_sec: float = 60.0) -> None:
        self._window = window_sec
        self._lock = threading.Lock()
        # key → deque of timestamps
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check(self, ip: str, group: str, limit: int) -> bool:
        """Return True if request is allowed, False if rate limit exceeded."""
        key = (ip, group)
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def cleanup(self) -> None:
        """Remove expired buckets (call periodically to avoid memory growth)."""
        cutoff = time.monotonic() - self._window
        with self._lock:
            stale = [k for k, dq in self._buckets.items() if not dq or dq[-1] < cutoff]
            for k in stale:
                del self._buckets[k]


# Global instance shared by all request threads
_limiter = RateLimiter(window_sec=60.0)

# Limits per group
LIMITS: dict[str, int] = {
    "jobs":    5,   # POST /api/jobs* — prevents run storm
    "config":  30,  # config reads/writes
    "default": 120, # everything else
}


def check_rate_limit(ip: str, path: str) -> tuple[bool, str]:
    """
    Check rate limit for the given IP and path.
    Returns (allowed, group_name).
    """
    if path.startswith("/api/jobs"):
        group, limit = "jobs", LIMITS["jobs"]
    elif path.startswith("/api/configs"):
        group, limit = "config", LIMITS["config"]
    else:
        group, limit = "default", LIMITS["default"]
    return _limiter.check(ip, group, limit), group
