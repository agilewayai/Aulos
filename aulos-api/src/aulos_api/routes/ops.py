from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field, field_serializer
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from aulos_api.auth.deps import require_roles
from aulos_api.db.models import EmailDeliveryLog, EmailToken, Role, User
from aulos_api.db.session import get_db
from aulos_api.services.mailgun import (
    effective_mail_provider,
    hash_token,
    list_recent_deliveries,
    load_mailgun_config,
    new_verification_token,
    save_mailgun_config,
    send_verification_email,
    test_mailgun_configuration,
    verification_expiry,
)
from aulos_api.services.llm_providers import (
    load_llm_config,
    save_llm_config,
    test_llm_provider,
)
from aulos_api.services.embeddings import load_embed_config, save_embed_config
from aulos_api.services.web_research import (
    load_web_research_config,
    public_web_research_config,
    save_web_research_config,
)
from aulos_api.services.discogs import (
    load_discogs_config,
    public_discogs_config,
    save_discogs_config,
)
from aulos_api.services.knowledge_base import knowledge_stats
from aulos_api.services.skills_ops import list_domain_skills, run_skill_probe, set_skill_enabled
from aulos_api.timefmt import to_utc_iso

router = APIRouter(prefix="/v1/ops", tags=["ops"])


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


class OpsUserOut(BaseModel):
    id: int
    email: str
    display_name: str
    email_verified: bool
    is_active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _ser_timestamps(self, value: datetime) -> str:
        return to_utc_iso(value)

class OpsUserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    email_verified: bool | None = None
    is_active: bool | None = None
    roles: list[str] | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: str
    user_count: int = 0


class OverviewOut(BaseModel):
    users_total: int
    users_active: int
    users_verified: int
    users_unverified: int
    users_inactive: int
    roles: dict[str, int]
    email_deliveries_total: int
    email_deliveries_failed: int
    mail_provider_mode: str
    mail_ready_for_live_send: bool
    llm_active_provider: str = "fake"
    llm_ready_for_live: bool = False


class ResendOut(BaseModel):
    ok: bool
    detail: str
    delivery_id: int | None = None


class DeleteUserRequest(BaseModel):
    confirm_email: EmailStr = Field(description="Must exactly match the target user email")


class DeleteUserOut(BaseModel):
    ok: bool
    deleted_user_id: int
    deleted_email: str
    detail: str


def _ops_user_out(user: User) -> OpsUserOut:
    return OpsUserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified,
        is_active=user.is_active,
        roles=sorted({r.name for r in user.roles}),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/overview", response_model=OverviewOut)
def get_overview(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> OverviewOut:
    users_total = db.query(func.count(User.id)).scalar() or 0
    users_active = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    users_verified = (
        db.query(func.count(User.id)).filter(User.email_verified.is_(True)).scalar() or 0
    )
    users_inactive = users_total - users_active
    users_unverified = users_total - users_verified

    role_counts: dict[str, int] = {}
    for role in db.query(Role).order_by(Role.name.asc()).all():
        role_counts[role.name] = len(role.users)

    deliveries_total = db.query(func.count(EmailDeliveryLog.id)).scalar() or 0
    deliveries_failed = (
        db.query(func.count(EmailDeliveryLog.id))
        .filter(EmailDeliveryLog.status == "failed")
        .scalar()
        or 0
    )
    cfg = load_mailgun_config(db)
    provider = effective_mail_provider(db)
    llm = load_llm_config(db)
    return OverviewOut(
        users_total=users_total,
        users_active=users_active,
        users_verified=users_verified,
        users_unverified=users_unverified,
        users_inactive=users_inactive,
        roles=role_counts,
        email_deliveries_total=deliveries_total,
        email_deliveries_failed=deliveries_failed,
        mail_provider_mode=provider,
        mail_ready_for_live_send=provider == "mailgun" and cfg.complete,
        llm_active_provider=llm.active_provider,
        llm_ready_for_live=llm.ready_for_live,
    )


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> list[RoleOut]:
    rows = db.query(Role).order_by(Role.name.asc()).all()
    return [
        RoleOut(
            id=role.id,
            name=role.name,
            description=role.description or "",
            user_count=len(role.users),
        )
        for role in rows
    ]


@router.get("/users", response_model=list[OpsUserOut])
def list_users(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="Search email or display name"),
    role: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    verified: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[OpsUserOut]:
    query = db.query(User).options(joinedload(User.roles))
    if q:
        needle = f"%{q.strip().lower()}%"
        query = query.filter(
            (func.lower(User.email).like(needle)) | (func.lower(User.display_name).like(needle))
        )
    if active is not None:
        query = query.filter(User.is_active.is_(active))
    if verified is not None:
        query = query.filter(User.email_verified.is_(verified))
    if role:
        query = query.join(User.roles).filter(Role.name == role.strip().lower())
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    return [_ops_user_out(u) for u in users]


@router.get("/users/{user_id}", response_model=OpsUserOut)
def get_user(
    user_id: int,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> OpsUserOut:
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user_id)
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _ops_user_out(user)


@router.patch("/users/{user_id}", response_model=OpsUserOut)
def patch_user(
    user_id: int,
    body: OpsUserUpdate,
    actor: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> OpsUserOut:
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user_id)
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.is_active is False and user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    if body.display_name is not None:
        user.display_name = body.display_name.strip() or user.display_name
    if body.email_verified is not None:
        user.email_verified = body.email_verified
    if body.is_active is not None:
        user.is_active = body.is_active

    if body.roles is not None:
        wanted = {name.strip().lower() for name in body.roles if name.strip()}
        if not wanted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one role is required",
            )
        if user.id == actor.id and "superadmin" not in wanted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove your own superadmin role",
            )
        roles = db.query(Role).filter(Role.name.in_(wanted)).all()
        found = {r.name for r in roles}
        missing = wanted - found
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown roles: {', '.join(sorted(missing))}",
            )
        if "user" not in found:
            # Keep base user role unless explicitly only assigning other known roles —
            # still require at least the roles requested; auto-include user for safety.
            base = db.query(Role).filter(Role.name == "user").one_or_none()
            if base is not None:
                roles.append(base)
        user.roles = roles

    db.commit()
    db.refresh(user)
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user.id)
        .one()
    )
    return _ops_user_out(user)


@router.post("/users/{user_id}/resend-verification", response_model=ResendOut)
def resend_verification(
    user_id: int,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> ResendOut:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email is already verified",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resend verification for inactive user",
        )

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
    try:
        send_verification_email(db=db, to_email=user.email, raw_token=raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send verification email: {exc}",
        ) from exc

    latest = (
        db.query(EmailDeliveryLog)
        .filter(EmailDeliveryLog.to_email == user.email, EmailDeliveryLog.kind == "verify_email")
        .order_by(EmailDeliveryLog.id.desc())
        .first()
    )
    return ResendOut(
        ok=True,
        detail="Verification email queued",
        delivery_id=latest.id if latest else None,
    )


@router.delete("/users/{user_id}", response_model=DeleteUserOut)
def delete_user(
    user_id: int,
    body: DeleteUserRequest,
    actor: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> DeleteUserOut:
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user_id)
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    confirm = str(body.confirm_email).strip().lower()
    if confirm != user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="confirm_email must match the user email exactly",
        )

    if user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    role_names = {r.name for r in user.roles}
    if "superadmin" in role_names:
        other_admins = (
            db.query(func.count(User.id))
            .join(User.roles)
            .filter(Role.name == "superadmin", User.id != user.id, User.is_active.is_(True))
            .scalar()
            or 0
        )
        if other_admins < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last active superadmin",
            )

    deleted_email = user.email
    deleted_id = user.id

    # Remove auth tokens and role links; scrub delivery PII for this mailbox.
    db.query(EmailToken).filter(EmailToken.user_id == user.id).delete(synchronize_session=False)
    user.roles = []
    redacted = f"deleted-user-{deleted_id}@redacted.invalid"
    for row in db.query(EmailDeliveryLog).filter(EmailDeliveryLog.to_email == deleted_email).all():
        row.to_email = redacted
        if deleted_email in (row.detail or ""):
            row.detail = (row.detail or "").replace(deleted_email, redacted)
        if deleted_email in (row.subject or ""):
            row.subject = (row.subject or "").replace(deleted_email, redacted)

    db.delete(user)
    db.commit()
    return DeleteUserOut(
        ok=True,
        deleted_user_id=deleted_id,
        deleted_email=deleted_email,
        detail="User permanently deleted; email tokens removed; delivery log PII scrubbed",
    )


@router.get("/mailgun", response_model=MailgunOut)
def get_mailgun(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> MailgunOut:
    cfg = load_mailgun_config(db)
    return MailgunOut(**cfg.public_dict(effective_provider=effective_mail_provider(db)))


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


class LlmProviderPublic(BaseModel):
    api_key_set: bool
    model: str
    base_url: str
    ready: bool


class LlmConfigOut(BaseModel):
    active_provider: str
    ready_for_live: bool
    deepseek: LlmProviderPublic
    grok: LlmProviderPublic
    supported_providers: list[str]


class LlmConfigUpdate(BaseModel):
    active_provider: str = Field(default="fake")
    deepseek_api_key: str | None = None
    deepseek_model: str | None = None
    deepseek_base_url: str | None = None
    grok_api_key: str | None = None
    grok_model: str | None = None
    grok_base_url: str | None = None


class LlmTestRequest(BaseModel):
    provider: str | None = Field(default=None, description="Optional provider override")


class LlmTestOut(BaseModel):
    ok: bool
    provider: str
    detail: str
    model: str = ""


@router.get("/llm", response_model=LlmConfigOut)
def get_llm(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> LlmConfigOut:
    return LlmConfigOut(**load_llm_config(db).public_dict())


@router.put("/llm", response_model=LlmConfigOut)
def put_llm(
    body: LlmConfigUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> LlmConfigOut:
    try:
        cfg = save_llm_config(
            db,
            active_provider=body.active_provider,
            deepseek_api_key=body.deepseek_api_key,
            deepseek_model=body.deepseek_model,
            deepseek_base_url=body.deepseek_base_url,
            grok_api_key=body.grok_api_key,
            grok_model=body.grok_model,
            grok_base_url=body.grok_base_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return LlmConfigOut(**cfg.public_dict())


@router.post("/llm/test", response_model=LlmTestOut)
async def post_llm_test(
    body: LlmTestRequest,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> LlmTestOut:
    try:
        result = await test_llm_provider(db=db, provider=body.provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM test failed: {exc}",
        ) from exc
    return LlmTestOut(**result)


class EmbedConfigOut(BaseModel):
    provider: str = "local"
    api_key_set: bool
    model: str
    base_url: str
    ready: bool
    supported_providers: list[str] = []
    local_default_model: str = ""
    fastembed_available: bool = False


class EmbedConfigUpdate(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None


@router.get("/embeddings", response_model=EmbedConfigOut)
def get_embeddings(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> EmbedConfigOut:
    return EmbedConfigOut(**load_embed_config(db).public_dict())


class WebResearchConfigOut(BaseModel):
    enabled: bool = True
    min_rag_hits: int = 3
    min_dossier_richness: int = 5
    refresh_after_hours: int = 168
    brave_api_key_set: bool = False
    persist_global: bool = True
    max_sources: int = 10
    agent_reach_enabled: bool = True


class WebResearchConfigUpdate(BaseModel):
    enabled: bool | None = None
    min_rag_hits: int | None = None
    min_dossier_richness: int | None = None
    refresh_after_hours: int | None = None
    brave_api_key: str | None = None
    persist_global: bool | None = None
    max_sources: int | None = None
    agent_reach_enabled: bool | None = None


@router.get("/web-research", response_model=WebResearchConfigOut)
def get_web_research(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> WebResearchConfigOut:
    return WebResearchConfigOut(**public_web_research_config(load_web_research_config(db)))


@router.put("/web-research", response_model=WebResearchConfigOut)
def put_web_research(
    body: WebResearchConfigUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> WebResearchConfigOut:
    cfg = save_web_research_config(
        db,
        enabled=body.enabled,
        min_rag_hits=body.min_rag_hits,
        min_dossier_richness=body.min_dossier_richness,
        refresh_after_hours=body.refresh_after_hours,
        brave_api_key=body.brave_api_key,
        persist_global=body.persist_global,
        max_sources=body.max_sources,
        agent_reach_enabled=body.agent_reach_enabled,
    )
    return WebResearchConfigOut(**cfg)


class DiscogsConfigOut(BaseModel):
    enabled: bool = True
    user_token_set: bool = False
    auth_source: str = "none"
    authenticated: bool = False


class DiscogsConfigUpdate(BaseModel):
    enabled: bool | None = None
    user_token: str | None = None
    clear_user_token: bool = False


@router.get("/discogs", response_model=DiscogsConfigOut)
def get_discogs(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> DiscogsConfigOut:
    return DiscogsConfigOut(**public_discogs_config(load_discogs_config(db)))


@router.put("/discogs", response_model=DiscogsConfigOut)
def put_discogs(
    body: DiscogsConfigUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> DiscogsConfigOut:
    cfg = save_discogs_config(
        db,
        user_token=body.user_token,
        clear_user_token=body.clear_user_token,
        enabled=body.enabled,
    )
    return DiscogsConfigOut(**cfg)


@router.put("/embeddings", response_model=EmbedConfigOut)
def put_embeddings(
    body: EmbedConfigUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> EmbedConfigOut:
    try:
        cfg = save_embed_config(
            db,
            provider=body.provider,
            api_key=body.api_key,
            model=body.model,
            base_url=body.base_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EmbedConfigOut(**cfg.public_dict())


@router.get("/knowledge/stats")
def ops_knowledge_stats(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> dict:
    """Legacy local SQLite KB counts + optional knowledge-plane health."""
    local = knowledge_stats(db)
    from aulos_api.services.knowledge_proxy import knowledge_enabled, knowledge_base_url

    out = {**local, "plane_enabled": knowledge_enabled(), "plane_url": knowledge_base_url()}
    return out


@router.api_route("/knowledge/plane/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def ops_knowledge_plane_proxy(
    path: str,
    request: Request,
    _: User = Depends(require_roles("superadmin")),
):
    """Proxy OPS Knowledge audit UI to aulos-knowledge (SPEC-010)."""
    from fastapi.responses import JSONResponse

    from aulos_api.services.knowledge_proxy import proxy_knowledge

    body = None
    if request.method.upper() in {"POST", "PUT", "PATCH"}:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = None
    status_code, data = await proxy_knowledge(
        request.method,
        f"/{path}",
        json_body=body,
        params=dict(request.query_params),
    )
    return JSONResponse(content=data, status_code=status_code)


class SkillOut(BaseModel):
    id: str
    name: str
    layer: str
    runtime: str = ""
    version: str
    summary: str
    triggers: list[str] = []
    observability_title: str = ""
    enabled: bool = True


class SkillProbeRequest(BaseModel):
    message: str = Field(default="I'm listening to Bach Goldberg Variations")


class SkillProbeOut(BaseModel):
    work_title: str
    composer: str
    summary: str
    steps: list[dict]
    skill_versions: dict[str, str]
    eval_pass: bool
    eval_score: int
    source: str
    guide_html_chars: int = 0
    context_keys: list[str] = []


@router.get("/skills", response_model=list[SkillOut])
def get_skills(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> list[SkillOut]:
    return [SkillOut(**row) for row in list_domain_skills(db)]


class SkillToggleRequest(BaseModel):
    enabled: bool


@router.patch("/skills/{skill_id}", response_model=SkillOut)
def patch_skill(
    skill_id: str,
    body: SkillToggleRequest,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> SkillOut:
    try:
        row = set_skill_enabled(db, skill_id, body.enabled)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SkillOut(**row)


@router.post("/skills/probe", response_model=SkillProbeOut)
def post_skills_probe(
    body: SkillProbeRequest,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> SkillProbeOut:
    try:
        result = run_skill_probe(body.message, db=db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Skill probe failed: {exc}",
        ) from exc
    return SkillProbeOut(**result)


class DbRoleIn(BaseModel):
    role: str  # primary | failover
    reason: str = "ops"


@router.get("/db/ha")
def ops_db_ha(_: User = Depends(require_roles("superadmin"))) -> dict:
    from aulos_api.services import db_ha

    return db_ha.ha_status()


@router.post("/db/sync")
def ops_db_sync(
    _: User = Depends(require_roles("superadmin")),
    queue: bool = Query(True),
) -> dict:
    """Enqueue primary→failover clone (Redis queue) or run inline if Redis down."""
    from aulos_api.services import db_ha

    if queue:
        return db_ha.enqueue_sync(trigger="ops")
    return db_ha.clone_primary_to_failover(trigger="ops-inline")


@router.post("/db/role")
def ops_db_role(body: DbRoleIn, _: User = Depends(require_roles("superadmin"))) -> dict:
    from aulos_api.services import db_ha

    try:
        role = db_ha.set_active_role(body.role, reason=body.reason or "ops")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True, "active_role": role, "status": db_ha.ha_status()}


# --- Daily product development blog (SPEC-009) ---


class DevBlogSummaryOut(BaseModel):
    day: str
    title: str
    provider: str
    generated_at: str
    evidence: dict = Field(default_factory=dict)


class DevBlogPostOut(DevBlogSummaryOut):
    body_md: str


class DevBlogGenerateIn(BaseModel):
    force: bool = False


@router.get("/dev-blog", response_model=list[DevBlogSummaryOut])
def list_dev_blog(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> list[DevBlogSummaryOut]:
    from aulos_api.services import dev_blog as blog

    return [DevBlogSummaryOut(**row) for row in blog.list_posts(db)]


@router.get("/dev-blog/{day}", response_model=DevBlogPostOut)
def get_dev_blog(
    day: str,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> DevBlogPostOut:
    from aulos_api.services import dev_blog as blog

    try:
        row = blog.get_post(db, day)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No blog for that day")
    return DevBlogPostOut(**blog.post_to_dict(row, include_body=True))


@router.post("/dev-blog/{day}/generate", response_model=DevBlogPostOut)
async def generate_dev_blog(
    day: str,
    body: DevBlogGenerateIn | None = None,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> DevBlogPostOut:
    from aulos_api.services import dev_blog as blog

    force = bool(body.force) if body else False
    try:
        row = await blog.generate_or_load(db, day, force=force)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return DevBlogPostOut(**blog.post_to_dict(row, include_body=True))
