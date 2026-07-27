"""Baseline security response headers for static host and proxied API routes."""

from __future__ import annotations

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "X-Frame-Options": "SAMEORIGIN",
}

PUBLIC_GUIDE_CSP = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'self'; "
    "script-src 'unsafe-inline' 'self' https://upload.wikimedia.org; "
    "style-src 'unsafe-inline' 'self'; "
    "img-src * data: blob:; "
    "media-src * blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'"
)
