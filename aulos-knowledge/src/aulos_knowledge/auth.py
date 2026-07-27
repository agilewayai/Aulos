"""Service-token auth for knowledge-plane admin routes (AUDIT-009 F5)."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from aulos_knowledge.config import get_settings


def require_admin_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = (settings.admin_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge admin token not configured",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin token required")
    token = authorization[7:].strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin token")
