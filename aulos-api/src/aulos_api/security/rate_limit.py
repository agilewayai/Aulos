"""In-process sliding-window rate limiter + abuse strike detection."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger("aulos_api.security")


@dataclass(frozen=True)
class RateRule:
    name: str
    limit: int
    window_sec: float


@dataclass
class RateDecision:
    allowed: bool
    remaining: int
    retry_after: float
    rule: str
    count: int


class SlidingWindowLimiter:
    """Thread-safe per-key sliding window counter."""

    def __init__(self, *, max_keys: int = 20_000) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._max_keys = max_keys

    def hit(self, key: str, *, limit: int, window_sec: float, now: float | None = None) -> RateDecision:
        now = time.monotonic() if now is None else now
        cutoff = now - window_sec
        with self._lock:
            bucket = self._prune(key, cutoff)
            count = len(bucket)
            if count >= limit:
                retry = max(0.0, (bucket[0] + window_sec) - now) if bucket else window_sec
                return RateDecision(
                    allowed=False,
                    remaining=0,
                    retry_after=retry,
                    rule=key.rsplit(":", 1)[0] if ":" in key else key,
                    count=count,
                )
            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return RateDecision(
                allowed=True,
                remaining=remaining,
                retry_after=0.0,
                rule=key.rsplit(":", 1)[0] if ":" in key else key,
                count=len(bucket),
            )

    def record(self, key: str, *, window_sec: float, now: float | None = None) -> int:
        """Always record an event; return current window count."""
        now = time.monotonic() if now is None else now
        cutoff = now - window_sec
        with self._lock:
            bucket = self._prune(key, cutoff)
            bucket.append(now)
            return len(bucket)

    def _prune(self, key: str, cutoff: float) -> deque[float]:
        if len(self._hits) > self._max_keys and key not in self._hits:
            self._evict_stale(cutoff)
        bucket = self._hits[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        return bucket

    def _evict_stale(self, cutoff: float) -> None:
        stale = [k for k, q in self._hits.items() if not q or q[-1] <= cutoff]
        for k in stale[: max(1, len(stale) // 2)]:
            self._hits.pop(k, None)


class AbuseDetector:
    """Count rate-limit strikes; escalate log level when an IP looks abusive."""

    def __init__(self, *, strike_limit: int = 8, window_sec: float = 300.0) -> None:
        self._limiter = SlidingWindowLimiter(max_keys=10_000)
        self.strike_limit = strike_limit
        self.window_sec = window_sec

    def note_block(self, *, ip: str, path: str, rule: str) -> bool:
        """Return True when this IP crossed the abuse threshold."""
        strikes = self._limiter.record(f"strike:{ip}", window_sec=self.window_sec)
        suspected = strikes >= self.strike_limit
        if suspected:
            logger.error(
                "abuse_suspected ip=%s path=%s rule=%s strikes=%s window_sec=%s",
                ip,
                path,
                rule,
                strikes,
                int(self.window_sec),
            )
        else:
            logger.warning(
                "rate_limit_exceeded ip=%s path=%s rule=%s strikes=%s",
                ip,
                path,
                rule,
                strikes,
            )
        return suspected

def client_ip(headers: dict[str, str], peer: str | None, *, trust_proxy: bool) -> str:
    if trust_proxy:
        forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        if forwarded:
            # Left-most is the original client when behind a trusted ingress.
            return forwarded.split(",")[0].strip() or (peer or "unknown")
        real_ip = headers.get("x-real-ip") or headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    return peer or "unknown"


RuleMatcher = Callable[[str, str], RateRule | None]


def default_api_rules(method: str, path: str) -> RateRule | None:
    """Path-aware limits — stricter on auth / LLM / public scrape surfaces."""
    if path in {"/health", "/docs", "/openapi.json", "/redoc"} or path.startswith("/docs/"):
        return None

    m = method.upper()
    if m == "POST" and path == "/v1/auth/login":
        return RateRule("auth_login", limit=10, window_sec=60)
    if m == "POST" and path == "/v1/auth/register":
        return RateRule("auth_register", limit=5, window_sec=60)
    if m == "POST" and path == "/v1/auth/verify-email":
        return RateRule("auth_verify", limit=20, window_sec=60)
    if m == "POST" and path == "/v1/chat":
        return RateRule("chat", limit=20, window_sec=60)
    if m == "POST" and path.endswith("/stream"):
        return RateRule("listening_stream", limit=8, window_sec=60)
    if m == "POST" and "/listening-guides/" in path and path.endswith("/update-publish"):
        return RateRule("listening_publish", limit=20, window_sec=60)
    if path.startswith("/v1/public/guides/"):
        return RateRule("public_guides", limit=60, window_sec=60)
    if path.startswith("/v1/media/"):
        return RateRule("media", limit=90, window_sec=60)
    if path.startswith("/v1/knowledge/"):
        return RateRule("knowledge", limit=30, window_sec=60)
    if path.startswith("/v1/ops/"):
        return RateRule("ops", limit=120, window_sec=60)
    if path.startswith("/v1/"):
        return RateRule("api_default", limit=120, window_sec=60)
    return RateRule("http_default", limit=180, window_sec=60)
