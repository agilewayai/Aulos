"""HttpOnly session cookie helpers (SPEC-014 / AUDIT-009 F3)."""

from __future__ import annotations

from fastapi import Response

from aulos_api.config import get_settings

SESSION_COOKIE_NAME = "aulos_session"


def _cookie_secure() -> bool:
    settings = get_settings()
    if settings.session_cookie_secure:
        return True
    return (settings.web_base_url or "").lower().startswith("https://")


def attach_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    max_age = int(settings.jwt_expire_minutes) * 60
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=_cookie_secure(),
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=_cookie_secure(),
        samesite=get_settings().session_cookie_samesite,
    )
