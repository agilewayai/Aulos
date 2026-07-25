"""Minimal sliding-window rate gate for the SPA static host (no third-party deps)."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque

logger = logging.getLogger("aulos.serve.security")


class RateGate:
    def __init__(self, *, max_keys: int = 20_000) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._max_keys = max_keys
        self._strikes: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, *, limit: int, window_sec: float) -> tuple[bool, float]:
        now = time.monotonic()
        cutoff = now - window_sec
        with self._lock:
            if len(self._hits) > self._max_keys and key not in self._hits:
                self._evict(self._hits, cutoff)
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry = max(0.0, (bucket[0] + window_sec) - now) if bucket else window_sec
                return False, retry
            bucket.append(now)
            return True, 0.0

    def note_block(self, ip: str, path: str, rule: str, *, strike_limit: int = 12, window_sec: float = 300.0) -> None:
        now = time.monotonic()
        cutoff = now - window_sec
        with self._lock:
            bucket = self._strikes[ip]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            bucket.append(now)
            strikes = len(bucket)
        if strikes >= strike_limit:
            logger.error(
                "abuse_suspected ip=%s path=%s rule=%s strikes=%s",
                ip,
                path,
                rule,
                strikes,
            )
        else:
            logger.warning(
                "rate_limit_exceeded ip=%s path=%s rule=%s strikes=%s",
                ip,
                path,
                rule,
                strikes,
            )

    @staticmethod
    def _evict(store: dict[str, deque[float]], cutoff: float) -> None:
        stale = [k for k, q in store.items() if not q or q[-1] <= cutoff]
        for k in stale[: max(1, len(stale) // 2)]:
            store.pop(k, None)


def client_ip(headers, peer: str | None, *, trust_proxy: bool = True) -> str:
    if trust_proxy:
        forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip() or (peer or "unknown")
        real_ip = headers.get("X-Real-IP") or headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
    return peer or "unknown"


def rule_for(path: str) -> tuple[str, int, float] | None:
    """Return (rule_name, limit, window_sec) for a request path."""
    raw = path.split("?", 1)[0]
    if raw == "/version.json":
        # Legitimate clients poll ~1/min; allow brief focus bursts.
        return ("version", 30, 60.0)
    if raw.startswith("/g/") or raw.startswith("/v1/public/"):
        return ("public_guide", 90, 60.0)
    if raw.startswith("/v1/auth/"):
        return ("auth_proxy", 30, 60.0)
    if raw.startswith("/v1/") or raw == "/health":
        if raw == "/health":
            return None
        return ("api_proxy", 180, 60.0)
    if "/assets/" in raw:
        return ("assets", 240, 60.0)
    return ("static", 120, 60.0)
