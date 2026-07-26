from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session, joinedload

from aulos_api.auth.deps import get_current_user
from aulos_api.auth.passwords import hash_password, verify_password
from aulos_api.auth.tokens import create_access_token
from aulos_api.db.models import EmailToken, Role, User
from aulos_api.db.session import get_db
from aulos_api.services.mailgun import (
    hash_token,
    new_verification_token,
    send_password_reset_email,
    send_verification_email,
    verification_expiry,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    token: str = Field(min_length=10)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordOut(BaseModel):
    ok: bool = True
    detail: str = (
        "If an account exists for that email, a password reset link has been sent."
    )


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordOut(BaseModel):
    ok: bool = True
    detail: str = "Password updated. You can sign in with your new password."


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    email_verified: bool
    roles: list[str]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified,
        roles=sorted({r.name for r in user.roles}),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> UserOut:
    email = body.email.lower().strip()
    existing = db.query(User).filter(User.email == email).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role = db.query(Role).filter(Role.name == "user").one_or_none()
    if role is None:
        raise HTTPException(status_code=500, detail="Roles not bootstrapped")

    user = User(
        email=email,
        display_name=body.display_name.strip() or email.split("@")[0],
        password_hash=hash_password(body.password),
        email_verified=False,
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.flush()

    raw = new_verification_token()
    db.add(
        EmailToken(
            user_id=user.id,
            purpose="verify_email",
            token_hash=hash_token(raw),
            expires_at=verification_expiry(),
        )
    )
    db.commit()
    db.refresh(user)

    try:
        send_verification_email(db=db, to_email=user.email, raw_token=raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to send verification email: {exc}") from exc

    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user.id)
        .one()
    )
    return _user_out(user)


@router.post("/verify-email", response_model=UserOut)
def verify_email(body: VerifyRequest, db: Session = Depends(get_db)) -> UserOut:
    token_hash = hash_token(body.token.strip())
    row = db.query(EmailToken).filter(EmailToken.token_hash == token_hash).one_or_none()
    if row is None or row.purpose != "verify_email":
        raise HTTPException(status_code=400, detail="Invalid verification token")
    if row.used_at is not None:
        raise HTTPException(status_code=400, detail="Verification token already used")
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification token expired")

    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == row.user_id)
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    user.email_verified = True
    row.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    email = body.email.lower().strip()
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.email == email)
        .one_or_none()
    )
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    roles = sorted({r.name for r in user.roles})
    token = create_access_token(subject=user.email, roles=roles)
    return TokenOut(access_token=token, user=_user_out(user))


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordOut:
    """Always return the same message — do not reveal whether the email exists."""
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is not None and user.is_active:
        # Invalidate prior unused reset tokens for this user
        now = datetime.now(timezone.utc)
        prior = (
            db.query(EmailToken)
            .filter(
                EmailToken.user_id == user.id,
                EmailToken.purpose == "reset_password",
                EmailToken.used_at.is_(None),
            )
            .all()
        )
        for row in prior:
            row.used_at = now

        raw = new_verification_token()
        db.add(
            EmailToken(
                user_id=user.id,
                purpose="reset_password",
                token_hash=hash_token(raw),
                expires_at=verification_expiry(),
            )
        )
        db.commit()
        try:
            send_password_reset_email(db=db, to_email=user.email, raw_token=raw)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502,
                detail=f"Failed to send password reset email: {exc}",
            ) from exc
    return ForgotPasswordOut()


@router.post("/reset-password", response_model=ResetPasswordOut)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)) -> ResetPasswordOut:
    token_hash = hash_token(body.token.strip())
    row = db.query(EmailToken).filter(EmailToken.token_hash == token_hash).one_or_none()
    if row is None or row.purpose != "reset_password":
        raise HTTPException(status_code=400, detail="Invalid reset token")
    if row.used_at is not None:
        raise HTTPException(status_code=400, detail="Reset token already used")
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token expired")

    user = db.query(User).filter(User.id == row.user_id).one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user.password_hash = hash_password(body.password)
    row.used_at = datetime.now(timezone.utc)
    db.commit()
    return ResetPasswordOut()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)
