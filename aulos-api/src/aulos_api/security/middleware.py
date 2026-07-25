"""ASGI rate-limit middleware with abuse logging."""

from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from aulos_api.security.rate_limit import (
    AbuseDetector,
    RateRule,
    SlidingWindowLimiter,
    client_ip,
    default_api_rules,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        trust_proxy: bool = True,
        match_rule: Callable[[str, str], RateRule | None] | None = None,
        limiter: SlidingWindowLimiter | None = None,
        abuse: AbuseDetector | None = None,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.trust_proxy = trust_proxy
        self.match_rule = match_rule or default_api_rules
        self.limiter = limiter or SlidingWindowLimiter()
        self.abuse = abuse or AbuseDetector()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        rule = self.match_rule(request.method, request.url.path)
        if rule is None:
            return await call_next(request)

        peer = request.client.host if request.client else None
        # Starlette headers are lowercase keys
        ip = client_ip(dict(request.headers), peer, trust_proxy=self.trust_proxy)
        key = f"{rule.name}:{ip}"
        decision = self.limiter.hit(key, limit=rule.limit, window_sec=rule.window_sec)
        if not decision.allowed:
            self.abuse.note_block(ip=ip, path=request.url.path, rule=rule.name)
            retry = max(1, int(decision.retry_after + 0.999))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "rule": rule.name,
                    "retry_after": retry,
                },
                headers={
                    "Retry-After": str(retry),
                    "X-RateLimit-Limit": str(rule.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Rule": rule.name,
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rule.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        response.headers["X-RateLimit-Rule"] = rule.name
        # Cheap clock skew for clients that care
        response.headers.setdefault("X-RateLimit-Reset", str(int(time.time() + rule.window_sec)))
        return response
