"""Ops-managed LLM providers for Aulos agent chat (DeepSeek + Grok)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

import httpx
from sqlalchemy.orm import Session

from aulos_api.db.models import SystemSetting

logger = logging.getLogger("aulos_api.llm")

LLM_SETTING_KEY = "llm.providers"

DEFAULT_DEEPSEEK_BASE = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_GROK_BASE = "https://api.x.ai/v1"
DEFAULT_GROK_MODEL = "grok-3-mini"

SUPPORTED_PROVIDERS = ("fake", "deepseek", "grok")

# Curated model catalogs for Ops dropdowns (id must match provider API model name).
PROVIDER_MODEL_OPTIONS: dict[str, list[dict[str, str]]] = {
    "deepseek": [
        {"id": "deepseek-chat", "label": "deepseek-chat (V3 — general)"},
        {"id": "deepseek-reasoner", "label": "deepseek-reasoner (R1 — thinking)"},
        {"id": "deepseek-v4-pro", "label": "deepseek-v4-pro"},
        {"id": "deepseek-v4-flash", "label": "deepseek-v4-flash"},
        {"id": "deepseek-coder", "label": "deepseek-coder"},
    ],
    "grok": [
        {"id": "grok-3-mini", "label": "grok-3-mini (fast / cheap)"},
        {"id": "grok-3", "label": "grok-3"},
        {"id": "grok-3-fast", "label": "grok-3-fast"},
        {"id": "grok-4", "label": "grok-4"},
        {"id": "grok-4-0709", "label": "grok-4-0709"},
        {"id": "grok-2-1212", "label": "grok-2-1212"},
        {"id": "grok-2-vision-1212", "label": "grok-2-vision-1212"},
    ],
}


def _env(*names: str) -> str:
    for name in names:
        val = (os.environ.get(name) or "").strip()
        if val:
            return val
    return ""


@dataclass
class ProviderCredentials:
    api_key: str = ""
    model: str = ""
    base_url: str = ""

    @classmethod
    def from_dict(cls, data: dict | None, *, default_model: str, default_base: str) -> ProviderCredentials:
        data = data or {}
        return cls(
            api_key=str(data.get("api_key") or ""),
            model=str(data.get("model") or default_model),
            base_url=str(data.get("base_url") or default_base).rstrip("/"),
        )

    @property
    def complete(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    def public_dict(self) -> dict:
        return {
            "api_key_set": bool(self.api_key),
            "model": self.model,
            "base_url": self.base_url,
            "ready": self.complete,
        }

    def to_storage(self) -> dict:
        return {
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
        }


@dataclass
class LlmProvidersConfig:
    active_provider: str = "fake"
    # Multi-agent split: draft ≠ review so critic cannot rubber-stamp the author model.
    draft_provider: str = "deepseek"
    review_provider: str = "grok"
    deepseek: ProviderCredentials = field(
        default_factory=lambda: ProviderCredentials(
            model=DEFAULT_DEEPSEEK_MODEL,
            base_url=DEFAULT_DEEPSEEK_BASE,
        )
    )
    grok: ProviderCredentials = field(
        default_factory=lambda: ProviderCredentials(
            model=DEFAULT_GROK_MODEL,
            base_url=DEFAULT_GROK_BASE,
        )
    )

    @classmethod
    def from_dict(cls, data: dict | None) -> LlmProvidersConfig:
        data = data or {}
        active = str(data.get("active_provider") or "fake").lower()
        if active not in SUPPORTED_PROVIDERS:
            active = "fake"
        draft = str(data.get("draft_provider") or "deepseek").lower()
        review = str(data.get("review_provider") or "grok").lower()
        if draft not in ("deepseek", "grok"):
            draft = "deepseek"
        if review not in ("deepseek", "grok"):
            review = "grok"
        return cls(
            active_provider=active,
            draft_provider=draft,
            review_provider=review,
            deepseek=ProviderCredentials.from_dict(
                data.get("deepseek") if isinstance(data.get("deepseek"), dict) else None,
                default_model=DEFAULT_DEEPSEEK_MODEL,
                default_base=DEFAULT_DEEPSEEK_BASE,
            ),
            grok=ProviderCredentials.from_dict(
                data.get("grok") if isinstance(data.get("grok"), dict) else None,
                default_model=DEFAULT_GROK_MODEL,
                default_base=DEFAULT_GROK_BASE,
            ),
        )

    def provider_creds(self, name: str | None = None) -> ProviderCredentials | None:
        provider = (name or self.active_provider).lower()
        if provider == "deepseek":
            return self.deepseek
        if provider == "grok":
            return self.grok
        return None

    def resolve_role_provider(self, role: str | None = None) -> str | None:
        """Map atelier role → live provider name.

        - draft: guide enrichment / author model (default DeepSeek)
        - review: Intent Critic + external_review (default Grok) — never silently
          falls back to the draft provider (anti rubber-stamp).
        - None/other: active_provider (chat / general)
        """
        role_l = (role or "").strip().lower()
        if role_l == "draft":
            preferred = self.draft_provider or "deepseek"
        elif role_l == "review":
            preferred = self.review_provider or "grok"
        else:
            preferred = self.active_provider
        if preferred == "fake":
            return None
        creds = self.provider_creds(preferred)
        if creds and creds.complete:
            if role_l == "review" and preferred == (self.draft_provider or "deepseek"):
                # Same provider as draft: only OK when operator explicitly set both equal.
                # Still allow if they intentionally matched; warn via return of preferred.
                pass
            return preferred
        if role_l == "review":
            # Do not fall back onto the draft author model.
            return None
        # draft / active: try the other live slot
        for name in ("deepseek", "grok"):
            if name == preferred:
                continue
            alt = self.provider_creds(name)
            if alt and alt.complete:
                return name
        return None

    @property
    def ready_for_live(self) -> bool:
        if self.active_provider == "fake":
            return False
        creds = self.provider_creds()
        return bool(creds and creds.complete)

    @property
    def ready_for_draft(self) -> bool:
        return self.resolve_role_provider("draft") is not None

    @property
    def ready_for_review(self) -> bool:
        return self.resolve_role_provider("review") is not None

    def public_dict(self) -> dict:
        return {
            "active_provider": self.active_provider,
            "draft_provider": self.draft_provider,
            "review_provider": self.review_provider,
            "ready_for_live": self.ready_for_live,
            "ready_for_draft": self.ready_for_draft,
            "ready_for_review": self.ready_for_review,
            "deepseek": self.deepseek.public_dict(),
            "grok": self.grok.public_dict(),
            "supported_providers": list(SUPPORTED_PROVIDERS),
            "model_options": {
                name: list(opts) for name, opts in PROVIDER_MODEL_OPTIONS.items()
            },
        }

    def to_storage(self) -> dict:
        return {
            "active_provider": self.active_provider,
            "draft_provider": self.draft_provider,
            "review_provider": self.review_provider,
            "deepseek": self.deepseek.to_storage(),
            "grok": self.grok.to_storage(),
        }

def apply_env_llm_overrides(cfg: LlmProvidersConfig) -> LlmProvidersConfig:
    """Merge host.env / process env into provider slots (key drop-in without Ops).

    Non-empty env values win for keys/model/base. Defaults keep Grok/DeepSeek
    slots ready so operators only need to paste a key later.
    """
    ds_key = _env("DEEPSEEK_API_KEY", "AULOS_DEEPSEEK_API_KEY")
    if ds_key:
        cfg.deepseek.api_key = ds_key
    ds_model = _env("AULOS_DEEPSEEK_MODEL", "DEEPSEEK_MODEL")
    if ds_model:
        cfg.deepseek.model = ds_model
    ds_base = _env("DEEPSEEK_BASE_URL", "AULOS_DEEPSEEK_BASE_URL")
    if ds_base:
        cfg.deepseek.base_url = ds_base.rstrip("/")
    if not cfg.deepseek.model:
        cfg.deepseek.model = DEFAULT_DEEPSEEK_MODEL
    if not cfg.deepseek.base_url:
        cfg.deepseek.base_url = DEFAULT_DEEPSEEK_BASE

    # Grok (xAI) — XAI_API_KEY is the canonical drop-in; AULOS_GROK_API_KEY alias OK.
    grok_key = _env("XAI_API_KEY", "AULOS_GROK_API_KEY")
    if grok_key:
        cfg.grok.api_key = grok_key
    grok_model = _env("AULOS_GROK_MODEL", "XAI_MODEL", "GROK_MODEL")
    if grok_model:
        cfg.grok.model = grok_model
    grok_base = _env("XAI_BASE_URL", "AULOS_GROK_BASE_URL", "GROK_BASE_URL")
    if grok_base:
        cfg.grok.base_url = grok_base.rstrip("/")
    if not cfg.grok.model:
        cfg.grok.model = DEFAULT_GROK_MODEL
    if not cfg.grok.base_url:
        cfg.grok.base_url = DEFAULT_GROK_BASE

    active = _env("AULOS_LLM_PROVIDER").lower()
    if active in SUPPORTED_PROVIDERS:
        cfg.active_provider = active
    draft = _env("AULOS_LLM_DRAFT_PROVIDER").lower()
    if draft in ("deepseek", "grok"):
        cfg.draft_provider = draft
    review = _env("AULOS_LLM_REVIEW_PROVIDER").lower()
    if review in ("deepseek", "grok"):
        cfg.review_provider = review
    return cfg


def load_llm_config(db: Session) -> LlmProvidersConfig:
    row = db.query(SystemSetting).filter(SystemSetting.key == LLM_SETTING_KEY).one_or_none()
    if row is None:
        cfg = LlmProvidersConfig()
    else:
        try:
            cfg = LlmProvidersConfig.from_dict(json.loads(row.value or "{}"))
        except json.JSONDecodeError:
            cfg = LlmProvidersConfig()
    return apply_env_llm_overrides(cfg)


def ensure_llm_provider_slots(db: Session) -> LlmProvidersConfig:
    """Persist default DeepSeek + Grok slots (model/base) so Ops is key-ready."""
    current = load_llm_config(db)
    # Strip env-only keys before persist — do not write process env secrets into DB
    # unless the row is brand new. Re-load raw storage then fill missing defaults.
    row = db.query(SystemSetting).filter(SystemSetting.key == LLM_SETTING_KEY).one_or_none()
    if row is None:
        stub = LlmProvidersConfig()
        payload = json.dumps(stub.to_storage())
        db.add(SystemSetting(key=LLM_SETTING_KEY, value=payload))
        db.commit()
        return apply_env_llm_overrides(stub)
    # Ensure nested grok/deepseek defaults exist in storage without wiping keys.
    try:
        raw = json.loads(row.value or "{}")
    except json.JSONDecodeError:
        raw = {}
    changed = False
    for name, default_model, default_base in (
        ("deepseek", DEFAULT_DEEPSEEK_MODEL, DEFAULT_DEEPSEEK_BASE),
        ("grok", DEFAULT_GROK_MODEL, DEFAULT_GROK_BASE),
    ):
        slot = raw.get(name) if isinstance(raw.get(name), dict) else {}
        if not isinstance(raw.get(name), dict):
            raw[name] = slot
            changed = True
        if not str(slot.get("model") or "").strip():
            slot["model"] = default_model
            changed = True
        if not str(slot.get("base_url") or "").strip():
            slot["base_url"] = default_base
            changed = True
        raw[name] = slot
    if "active_provider" not in raw:
        raw["active_provider"] = "fake"
        changed = True
    if not str(raw.get("draft_provider") or "").strip():
        raw["draft_provider"] = "deepseek"
        changed = True
    if not str(raw.get("review_provider") or "").strip():
        raw["review_provider"] = "grok"
        changed = True
    if changed:
        row.value = json.dumps(raw)
        db.commit()
    return load_llm_config(db)


def save_llm_config(
    db: Session,
    *,
    active_provider: str,
    draft_provider: str | None = None,
    review_provider: str | None = None,
    deepseek_api_key: str | None = None,
    deepseek_model: str | None = None,
    deepseek_base_url: str | None = None,
    grok_api_key: str | None = None,
    grok_model: str | None = None,
    grok_base_url: str | None = None,
) -> LlmProvidersConfig:
    current = load_llm_config(db)
    active = (active_provider or "fake").lower()
    if active not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {active_provider}")
    current.active_provider = active
    if draft_provider is not None and draft_provider.strip():
        draft = draft_provider.strip().lower()
        if draft not in ("deepseek", "grok"):
            raise ValueError(f"Unsupported draft_provider: {draft_provider}")
        current.draft_provider = draft
    if review_provider is not None and review_provider.strip():
        review = review_provider.strip().lower()
        if review not in ("deepseek", "grok"):
            raise ValueError(f"Unsupported review_provider: {review_provider}")
        current.review_provider = review

    if deepseek_api_key is not None and deepseek_api_key != "":
        current.deepseek.api_key = deepseek_api_key
    if deepseek_model is not None and deepseek_model.strip():
        current.deepseek.model = deepseek_model.strip()
    if deepseek_base_url is not None and deepseek_base_url.strip():
        current.deepseek.base_url = deepseek_base_url.strip().rstrip("/")

    if grok_api_key is not None and grok_api_key != "":
        current.grok.api_key = grok_api_key
    if grok_model is not None and grok_model.strip():
        current.grok.model = grok_model.strip()
    if grok_base_url is not None and grok_base_url.strip():
        current.grok.base_url = grok_base_url.strip().rstrip("/")

    payload = json.dumps(current.to_storage())
    row = db.query(SystemSetting).filter(SystemSetting.key == LLM_SETTING_KEY).one_or_none()
    if row is None:
        db.add(SystemSetting(key=LLM_SETTING_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    return current


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


async def invoke_openai_compatible(
    *,
    provider: str,
    creds: ProviderCredentials,
    message: str,
    system_prompt: str = "You are Aulos, a helpful assistant.",
    timeout: float = 60.0,
) -> str:
    url = _chat_completions_url(creds.base_url)
    headers = {
        "Authorization": f"Bearer {creds.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": creds.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "temperature": 0.3,
    }
    logger.info(
        "llm_invoke_start provider=%s model=%s base=%s",
        provider,
        creds.model,
        creds.base_url,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            detail = response.text[:500]
            logger.error(
                "llm_invoke_fail provider=%s status=%s detail=%s",
                provider,
                response.status_code,
                detail,
            )
            raise RuntimeError(f"{provider} API error ({response.status_code}): {detail}")
        data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"{provider} returned unexpected response shape") from exc
    text = str(content or "").strip()
    logger.info("llm_invoke_ok provider=%s chars=%s", provider, len(text))
    return text


async def chat_with_ops_llm(
    *,
    db: Session,
    message: str,
    timeout: float = 60.0,
    system_prompt: str = "You are Aulos, a helpful assistant.",
    role: str | None = None,
    provider: str | None = None,
) -> tuple[str, str] | None:
    """Return (reply, provider) when a live provider is ready; else None.

    role='draft' → draft_provider (DeepSeek by default)
    role='review' → review_provider (Grok by default; no same-model fallback)
    """
    cfg = load_llm_config(db)
    name = (provider or "").strip().lower() or cfg.resolve_role_provider(role)
    if not name or name == "fake":
        return None
    creds = cfg.provider_creds(name)
    if creds is None or not creds.complete:
        return None
    reply = await invoke_openai_compatible(
        provider=name,
        creds=creds,
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
    )
    return reply, name


async def test_llm_provider(*, db: Session, provider: str | None = None) -> dict:
    cfg = load_llm_config(db)
    name = (provider or cfg.active_provider).lower()
    if name == "fake":
        return {
            "ok": True,
            "provider": "fake",
            "detail": "Fake provider — no live API call performed",
            "model": "",
        }
    if name not in ("deepseek", "grok"):
        raise ValueError(f"Unsupported provider: {name}")
    creds = cfg.provider_creds(name)
    if creds is None or not creds.complete:
        raise ValueError(f"{name} is not fully configured (api key, model, base URL required)")
    reply = await invoke_openai_compatible(
        provider=name,
        creds=creds,
        message="Reply with exactly: ok",
        system_prompt="You are a connectivity probe. Reply briefly.",
    )
    return {
        "ok": True,
        "provider": name,
        "detail": f"Live probe succeeded: {reply[:200]}",
        "model": creds.model,
    }
