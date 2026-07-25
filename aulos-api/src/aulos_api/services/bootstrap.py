from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from aulos_api.auth.passwords import hash_password
from aulos_api.config import get_settings
from aulos_api.db import session as db_session
from aulos_api.db.models import Role, User
from aulos_api.db.session import init_db

DEFAULT_ROLES = (
    ("user", "Standard Aulos user"),
    ("superadmin", "Ops portal administrator"),
)


def ensure_roles(db: Session) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for name, description in DEFAULT_ROLES:
        role = db.query(Role).filter(Role.name == name).one_or_none()
        if role is None:
            role = Role(name=name, description=description)
            db.add(role)
            db.flush()
        roles[name] = role
    db.commit()
    return roles


def ensure_bootstrap_superadmin(db: Session, roles: dict[str, Role]) -> User | None:
    settings = get_settings()
    email = (settings.bootstrap_superadmin_email or "").strip().lower()
    password = settings.bootstrap_superadmin_password or ""
    if not email or not password:
        return None

    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.email == email)
        .one_or_none()
    )
    if user is None:
        user = User(
            email=email,
            display_name="Superadmin",
            password_hash=hash_password(password),
            email_verified=True,
            is_active=True,
        )
        user.roles.append(roles["superadmin"])
        if roles["user"] not in user.roles:
            user.roles.append(roles["user"])
        db.add(user)
    else:
        names = {r.name for r in user.roles}
        if "superadmin" not in names:
            user.roles.append(roles["superadmin"])
        user.email_verified = True
        user.is_active = True
    db.commit()
    db.refresh(user)
    return user


def bootstrap_identity() -> None:
    init_db()
    db_session.get_engine()
    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        roles = ensure_roles(db)
        ensure_bootstrap_superadmin(db, roles)
    finally:
        db.close()
