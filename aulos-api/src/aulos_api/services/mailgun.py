from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from aulos_api.config import get_settings
from aulos_api.db.models import EmailDeliveryLog, SystemSetting
from aulos_api.timefmt import to_utc_iso

logger = logging.getLogger("aulos_api.mail")

MAILGUN_SETTING_KEY = "mailgun.config"
_FAKE_MAILBOX: list[dict] = []

MAILGUN_API_BASE = {
    "us": "https://api.mailgun.net",
    "eu": "https://api.eu.mailgun.net",
}


@dataclass
class MailgunConfig:
    api_key: str = ""
    domain: str = ""
    from_email: str = ""
    enabled: bool = False
    region: str = "us"  # us | eu

    @classmethod
    def from_dict(cls, data: dict | None) -> MailgunConfig:
        data = data or {}
        region = str(data.get("region") or "us").lower()
        if region not in MAILGUN_API_BASE:
            region = "us"
        return cls(
            api_key=str(data.get("api_key") or ""),
            domain=str(data.get("domain") or ""),
            from_email=str(data.get("from_email") or ""),
            enabled=bool(data.get("enabled", False)),
            region=region,
        )

    @property
    def complete(self) -> bool:
        return bool(self.api_key and self.domain and self.from_email)

    def public_dict(self, *, effective_provider: str) -> dict:
        return {
            "domain": self.domain,
            "from_email": self.from_email,
            "enabled": self.enabled,
            "api_key_set": bool(self.api_key),
            "region": self.region,
            "provider_mode": effective_provider,
            "env_mail_provider": get_settings().mail_provider,
            "ready_for_live_send": self.enabled and self.complete,
        }


def get_fake_mailbox() -> list[dict]:
    return _FAKE_MAILBOX


def clear_fake_mailbox() -> None:
    _FAKE_MAILBOX.clear()


def load_mailgun_config(db: Session) -> MailgunConfig:
    row = db.query(SystemSetting).filter(SystemSetting.key == MAILGUN_SETTING_KEY).one_or_none()
    if row is None:
        return MailgunConfig()
    try:
        return MailgunConfig.from_dict(json.loads(row.value or "{}"))
    except json.JSONDecodeError:
        return MailgunConfig()


def save_mailgun_config(
    db: Session,
    *,
    api_key: str | None,
    domain: str,
    from_email: str,
    enabled: bool,
    region: str = "us",
) -> MailgunConfig:
    current = load_mailgun_config(db)
    if api_key is not None and api_key != "":
        current.api_key = api_key
    current.domain = domain
    current.from_email = from_email
    current.enabled = enabled
    region = (region or "us").lower()
    current.region = region if region in MAILGUN_API_BASE else "us"
    payload = json.dumps(
        {
            "api_key": current.api_key,
            "domain": current.domain,
            "from_email": current.from_email,
            "enabled": current.enabled,
            "region": current.region,
        }
    )
    row = db.query(SystemSetting).filter(SystemSetting.key == MAILGUN_SETTING_KEY).one_or_none()
    if row is None:
        row = SystemSetting(key=MAILGUN_SETTING_KEY, value=payload)
        db.add(row)
    else:
        row.value = payload
    db.commit()
    return current


def effective_mail_provider(db: Session) -> str:
    """Resolve whether to send via fake mailbox or live Mailgun.

    - `fake`: always in-memory (tests / offline)
    - `mailgun`: always attempt live Mailgun
    - `auto` (default for deploy): live Mailgun when ops config is enabled+complete
    """
    settings = get_settings()
    mode = (settings.mail_provider or "auto").strip().lower()
    if mode == "fake":
        return "fake"
    cfg = load_mailgun_config(db)
    if mode == "auto":
        if cfg.enabled and cfg.complete:
            return "mailgun"
        return "fake"
    if mode == "mailgun":
        return "mailgun"
    return "fake"


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_verification_token() -> str:
    return secrets.token_urlsafe(32)


def _record_delivery(
    db: Session,
    *,
    kind: str,
    to_email: str,
    subject: str,
    provider: str,
    status: str,
    detail: str = "",
    provider_message_id: str = "",
) -> EmailDeliveryLog:
    row = EmailDeliveryLog(
        kind=kind,
        to_email=to_email,
        subject=subject,
        provider=provider,
        status=status,
        detail=(detail or "")[:2000],
        provider_message_id=(provider_message_id or "")[:255],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_recent_deliveries(db: Session, *, limit: int = 50) -> list[EmailDeliveryLog]:
    return (
        db.query(EmailDeliveryLog)
        .order_by(EmailDeliveryLog.created_at.desc())
        .limit(limit)
        .all()
    )


def send_verification_email(*, db: Session, to_email: str, raw_token: str) -> None:
    settings = get_settings()
    verify_url = f"{settings.web_base_url.rstrip('/')}/verify?token={raw_token}"
    subject = "Verify your Aulos account"
    text = (
        "Welcome to Aulos.\n\n"
        f"Verify your email by opening:\n{verify_url}\n\n"
        "If you did not register, ignore this message.\n"
    )
    _send_message(
        db=db,
        to_email=to_email,
        subject=subject,
        text=text,
        kind="verify_email",
        extra={"verification_token": raw_token, "verify_url": verify_url},
    )


def test_mailgun_configuration(*, db: Session, to_email: str) -> dict:
    """Validate saved Mailgun settings and send a probe message."""
    cfg = load_mailgun_config(db)
    provider = effective_mail_provider(db)
    missing = [
        name
        for name, ok in (
            ("api_key", bool(cfg.api_key)),
            ("domain", bool(cfg.domain)),
            ("from_email", bool(cfg.from_email)),
            ("enabled", cfg.enabled),
        )
        if not ok
    ]
    if missing:
        raise ValueError("Mailgun is not fully configured: missing " + ", ".join(missing))

    subject = "Aulos Mailgun configuration test"
    text = (
        "This is a test message from Aulos Ops.\n\n"
        "If you received it, Mailgun configuration is working.\n"
    )
    result = _send_message(
        db=db,
        to_email=to_email,
        subject=subject,
        text=text,
        kind="config_test",
        extra={"domain": cfg.domain, "from_email": cfg.from_email},
    )
    detail = result.get("detail") or f"Test message accepted for {to_email}"
    if provider == "fake":
        detail = (
            f"FAKE provider accepted message for {to_email} "
            "(no real email sent). Set AULOS_MAIL_PROVIDER=auto and enable Mailgun to send live."
        )
    return {
        "ok": True,
        "provider_mode": provider,
        "detail": detail,
        "domain": cfg.domain,
        "from_email": cfg.from_email,
        "region": cfg.region,
        "delivery_id": result.get("delivery_id"),
    }


def _send_message(
    *,
    db: Session,
    to_email: str,
    subject: str,
    text: str,
    kind: str,
    extra: dict | None = None,
) -> dict:
    provider = effective_mail_provider(db)
    logger.info(
        "mail_send_start kind=%s to=%s provider=%s",
        kind,
        to_email,
        provider,
    )

    if provider == "fake":
        entry = {
            "to": to_email,
            "subject": subject,
            "text": text,
            "kind": kind,
            "sent_at": to_utc_iso(datetime.now(timezone.utc)),
        }
        if extra:
            entry.update(extra)
        _FAKE_MAILBOX.append(entry)
        row = _record_delivery(
            db,
            kind=kind,
            to_email=to_email,
            subject=subject,
            provider="fake",
            status="accepted_fake",
            detail="Stored in fake mailbox (no external delivery)",
        )
        logger.info("mail_send_ok kind=%s to=%s provider=fake delivery_id=%s", kind, to_email, row.id)
        return {"delivery_id": row.id, "provider": "fake", "detail": row.detail}

    cfg = load_mailgun_config(db)
    if not cfg.enabled or not cfg.complete:
        row = _record_delivery(
            db,
            kind=kind,
            to_email=to_email,
            subject=subject,
            provider="mailgun",
            status="failed",
            detail="Mailgun is not configured or disabled",
        )
        logger.error("mail_send_fail kind=%s to=%s reason=not_configured delivery_id=%s", kind, to_email, row.id)
        raise RuntimeError("Mailgun is not configured or disabled")

    base = MAILGUN_API_BASE.get(cfg.region, MAILGUN_API_BASE["us"])
    url = f"{base}/v3/{cfg.domain}/messages"
    try:
        response = httpx.post(
            url,
            auth=("api", cfg.api_key),
            data={
                "from": cfg.from_email,
                "to": [to_email],
                "subject": subject,
                "text": text,
            },
            timeout=30.0,
        )
        body_text = response.text
        message_id = ""
        try:
            payload = response.json()
            message_id = str(payload.get("id") or "")
        except Exception:  # noqa: BLE001
            payload = {}

        if response.is_success:
            row = _record_delivery(
                db,
                kind=kind,
                to_email=to_email,
                subject=subject,
                provider="mailgun",
                status="sent",
                detail=str(payload.get("message") or "Mailgun accepted message"),
                provider_message_id=message_id,
            )
            logger.info(
                "mail_send_ok kind=%s to=%s provider=mailgun region=%s domain=%s delivery_id=%s msg_id=%s",
                kind,
                to_email,
                cfg.region,
                cfg.domain,
                row.id,
                message_id,
            )
            return {
                "delivery_id": row.id,
                "provider": "mailgun",
                "detail": row.detail,
                "provider_message_id": message_id,
            }

        detail = f"Mailgun HTTP {response.status_code}: {body_text[:500]}"
        row = _record_delivery(
            db,
            kind=kind,
            to_email=to_email,
            subject=subject,
            provider="mailgun",
            status="failed",
            detail=detail,
        )
        logger.error(
            "mail_send_fail kind=%s to=%s status=%s delivery_id=%s detail=%s",
            kind,
            to_email,
            response.status_code,
            row.id,
            detail,
        )
        raise RuntimeError(detail)
    except httpx.HTTPError as exc:
        detail = f"Mailgun transport error: {exc}"
        row = _record_delivery(
            db,
            kind=kind,
            to_email=to_email,
            subject=subject,
            provider="mailgun",
            status="failed",
            detail=detail,
        )
        logger.exception("mail_send_fail kind=%s to=%s delivery_id=%s", kind, to_email, row.id)
        raise RuntimeError(detail) from exc


def verification_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(timezone.utc) + timedelta(hours=settings.verification_ttl_hours)
