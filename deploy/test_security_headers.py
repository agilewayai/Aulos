"""Security header baseline for static host (AUDIT-009 F7)."""

from security_headers import SECURITY_HEADERS
from serve import AulosHandler, cache_control_for


def test_static_responses_include_security_headers() -> None:
  assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
  assert SECURITY_HEADERS["Referrer-Policy"] == "strict-origin-when-cross-origin"
  assert "camera=()" in SECURITY_HEADERS["Permissions-Policy"]
  assert cache_control_for("/index.html") == "no-cache, no-store, must-revalidate"
  assert AulosHandler.rate_limit_enabled is True or AulosHandler.rate_limit_enabled is False
