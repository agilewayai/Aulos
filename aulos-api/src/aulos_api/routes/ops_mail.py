"""Ops Mailgun routes (AUDIT-009 F10)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_serializer
from sqlalchemy.orm import Session

from aulos_api.auth.deps import require_roles
from aulos_api.db.models import User
from aulos_api.db.session import get_db
from aulos_api.services.mailgun import (
    effective_mail_provider,
    list_recent_deliveries,
    load_mailgun_config,
    save_mailgun_config,
    test_mailgun_configuration,
)
from aulos_api.timefmt import to_utc_iso

router = APIRouter()


class MailgunOut(BaseModel):
    domain: str
    from_email: str
    enabled: bool
    api_key_set: bool
    region: str = "us"
    provider_mode: str
    env_mail_provider: str = "auto"
    ready_for_live_send: bool = False


class MailgunUpdate(BaseModel):
    api_key: str | None = Field(default=None, description="Omit or blank to keep existing key")
    domain: str = Field(default="")
    from_email: EmailStr | str = Field(default="")
    enabled: bool = False
    region: str = Field(default="us", description="us or eu")


class MailgunTestRequest(BaseModel):
    to_email: EmailStr


class MailgunTestOut(BaseModel):
    ok: bool
    provider_mode: str
    detail: str
    domain: str = ""
    from_email: str = ""
    region: str = "us"
    delivery_id: int | None = None


class DeliveryOut(BaseModel):
    id: int
    kind: str
    to_email: str
    subject: str
    provider: str
    status: str
    detail: str
    provider_message_id: str
    created_at: datetime

    @field_serializer("created_at")
    def _ser_created_at(self, value: datetime) -> str:
        return to_utc_iso(value)


@router.get("/mailgun", response_model=MailgunOut)
def get_mailgun(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> MailgunOut:
    cfg = load_mailgun_config(db)
    return MailgunOut(**cfg.public_dict(effective_provider=effective_mail_provider(db)))


@router.get("/mail/queue")
def get_mail_queue(_: User = Depends(require_roles("superadmin"))) -> dict:
    from aulos_api.services.mail_queue import queue_status

    return queue_status()


@router.put("/mailgun", response_model=MailgunOut)
def put_mailgun(
    body: MailgunUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> MailgunOut:
    cfg = save_mailgun_config(
        db,
        api_key=body.api_key,
        domain=body.domain.strip(),
        from_email=str(body.from_email).strip(),
        enabled=body.enabled,
        region=body.region,
    )
    return MailgunOut(**cfg.public_dict(effective_provider=effective_mail_provider(db)))


@router.post("/mailgun/test", response_model=MailgunTestOut)
def post_mailgun_test(
    body: MailgunTestRequest,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> MailgunTestOut:
    try:
        result = test_mailgun_configuration(db=db, to_email=str(body.to_email).strip().lower())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Mailgun test failed: {exc}",
        ) from exc
    return MailgunTestOut(**result)


@router.get("/mailgun/deliveries", response_model=list[DeliveryOut])
def get_mailgun_deliveries(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> list[DeliveryOut]:
    rows = list_recent_deliveries(db, limit=50)
    return [
        DeliveryOut(
            id=row.id,
            kind=row.kind,
            to_email=row.to_email,
            subject=row.subject,
            provider=row.provider,
            status=row.status,
            detail=row.detail,
            provider_message_id=row.provider_message_id,
            created_at=row.created_at,
        )
        for row in rows
    ]
