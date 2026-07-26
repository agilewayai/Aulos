"""Ops-managed LLM providers for Aulos agent chat (DeepSeek + Grok)."""

from __future__ import annotations

import json
import logging
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
        return cls(
            active_provider=active,
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

    @property
    def ready_for_live(self) -> bool:
        if self.active_provider == "fake":
            return False
        creds = self.provider_creds()
        return bool(creds and creds.complete)

    def public_dict(self) -> dict:
        return {
            "active_provider": self.active_provider,
            "ready_for_live": self.ready_for_live,
            "deepseek": self.deepseek.public_dict(),
            "grok": self.grok.public_dict(),
            "supported_providers": list(SUPPORTED_PROVIDERS),
        }

    def to_storage(self) -> dict:
        return {
            "active_provider": self.active_provider,
            "deepseek": self.deepseek.to_storage(),
            "grok": self.grok.to_storage(),
        }


def load_llm_config(db: Session) -> LlmProvidersConfig:
    row = db.query(SystemSetting).filter(SystemSetting.key == LLM_SETTING_KEY).one_or_none()
    if row is None:
        return LlmProvidersConfig()
    try:
        return LlmProvidersConfig.from_dict(json.loads(row.value or "{}"))
    except json.JSONDecodeError:
        return LlmProvidersConfig()


def save_llm_config(
    db: Session,
    *,
    active_provider: str,
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
) -> tuple[str, str] | None:
    """Return (reply, provider) when ops has a live provider; else None."""
    cfg = load_llm_config(db)
    if cfg.active_provider == "fake" or not cfg.ready_for_live:
        return None
    creds = cfg.provider_creds()
    if creds is None or not creds.complete:
        return None
    reply = await invoke_openai_compatible(
        provider=cfg.active_provider,
        creds=creds,
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
    )
    return reply, cfg.active_provider


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
