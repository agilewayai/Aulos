from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from aulos_api.auth.session import SESSION_COOKIE_NAME
from aulos_api.auth.tokens import decode_access_token
from aulos_api.db.models import User
from aulos_api.db.session import get_db

_bearer = HTTPBearer(auto_error=False)


def _resolve_access_token(
    request: Request,
    creds: HTTPAuthorizationCredentials | None,
) -> str | None:
    if creds is not None and creds.credentials:
        return creds.credentials
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    return cookie or None


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    token = _resolve_access_token(request, creds)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        email = str(payload.get("sub") or "")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.email == email.lower())
        .one_or_none()
    )
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*required: str):
    required_set = set(required)

    def _dep(user: User = Depends(get_current_user)) -> User:
        names = {r.name for r in user.roles}
        if not required_set.issubset(names):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _dep
