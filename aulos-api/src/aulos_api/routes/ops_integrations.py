"""Ops provider-config routes: LLM, embeddings, web-research, Discogs (AUDIT-009 F10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import require_roles
from aulos_api.db.models import User
from aulos_api.db.session import get_db
from aulos_api.services.discogs import (
    load_discogs_config,
    public_discogs_config,
    save_discogs_config,
)
from aulos_api.services.embeddings import load_embed_config, save_embed_config
from aulos_api.services.llm_providers import (
    load_llm_config,
    save_llm_config,
    test_llm_provider,
)
from aulos_api.services.listening_ambient import (
    public_ambient_fallback_config,
    save_ambient_fallback_mode,
)
from aulos_api.services.listening_review import (
    public_review_config,
    save_review_llm_enabled,
)
from aulos_api.services.web_research import (
    load_web_research_config,
    public_web_research_config,
    save_web_research_config,
)

router = APIRouter()


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


class ListeningReviewOut(BaseModel):
    key: str
    enabled: bool


class ListeningReviewUpdate(BaseModel):
    enabled: bool = True


@router.get("/listening-review", response_model=ListeningReviewOut)
def get_listening_review(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> ListeningReviewOut:
    return ListeningReviewOut(**public_review_config(db))


@router.put("/listening-review", response_model=ListeningReviewOut)
def put_listening_review(
    body: ListeningReviewUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> ListeningReviewOut:
    enabled = save_review_llm_enabled(db, enabled=body.enabled)
    return ListeningReviewOut(key="listening.review_llm", enabled=enabled)


class AmbientFallbackOut(BaseModel):
    key: str
    mode: str
    allowed: list[str]


class AmbientFallbackUpdate(BaseModel):
    mode: str = "embed"


@router.get("/ambient-fallback", response_model=AmbientFallbackOut)
def get_ambient_fallback(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> AmbientFallbackOut:
    return AmbientFallbackOut(**public_ambient_fallback_config(db))


@router.put("/ambient-fallback", response_model=AmbientFallbackOut)
def put_ambient_fallback(
    body: AmbientFallbackUpdate,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> AmbientFallbackOut:
    mode = save_ambient_fallback_mode(db, mode=body.mode)
    return AmbientFallbackOut(**public_ambient_fallback_config(db) | {"mode": mode})


