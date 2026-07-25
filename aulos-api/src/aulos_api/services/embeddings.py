"""Embeddings: local FastEmbed (default) + optional OpenAI-compatible remote."""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from aulos_api.db.models import SystemSetting

logger = logging.getLogger("aulos_api.embeddings")

EMBED_SETTING_KEY = "llm.embeddings"
SUPPORTED_PROVIDERS = ("local", "openai_compatible")

# Multilingual (EN+ZH) — good for Salon Codex 导赏 RAG
DEFAULT_LOCAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_REMOTE_MODEL = "text-embedding-3-small"
DEFAULT_REMOTE_BASE = "https://api.openai.com/v1"

_fastembed_cache: dict[str, Any] = {}


@dataclass
class EmbeddingConfig:
    provider: str = "local"
    api_key: str = ""
    model: str = DEFAULT_LOCAL_MODEL
    base_url: str = DEFAULT_REMOTE_BASE

    @classmethod
    def from_dict(cls, data: dict | None) -> EmbeddingConfig:
        data = data or {}
        provider = str(data.get("provider") or "local").lower().strip()
        if provider not in SUPPORTED_PROVIDERS:
            # Backward compat: old configs without provider but with api_key → remote
            if data.get("api_key"):
                provider = "openai_compatible"
            else:
                provider = "local"
        if provider == "local":
            default_model = DEFAULT_LOCAL_MODEL
        else:
            default_model = DEFAULT_REMOTE_MODEL
        return cls(
            provider=provider,
            api_key=str(data.get("api_key") or ""),
            model=str(data.get("model") or default_model),
            base_url=str(data.get("base_url") or DEFAULT_REMOTE_BASE).rstrip("/"),
        )

    @property
    def ready(self) -> bool:
        if self.provider == "local":
            return bool(self.model) and _fastembed_available()
        return bool(self.api_key and self.model and self.base_url)

    def public_dict(self) -> dict:
        return {
            "provider": self.provider,
            "api_key_set": bool(self.api_key),
            "model": self.model,
            "base_url": self.base_url,
            "ready": self.ready,
            "supported_providers": list(SUPPORTED_PROVIDERS),
            "local_default_model": DEFAULT_LOCAL_MODEL,
            "fastembed_available": _fastembed_available(),
        }

    def to_storage(self) -> dict:
        return {
            "provider": self.provider,
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
        }


def _fastembed_available() -> bool:
    try:
        import fastembed  # noqa: F401
        return True
    except ImportError:
        return False


def load_embed_config(db: Session) -> EmbeddingConfig:
    row = db.query(SystemSetting).filter(SystemSetting.key == EMBED_SETTING_KEY).one_or_none()
    if row is None:
        return EmbeddingConfig()
    try:
        return EmbeddingConfig.from_dict(json.loads(row.value or "{}"))
    except json.JSONDecodeError:
        return EmbeddingConfig()


def save_embed_config(
    db: Session,
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> EmbeddingConfig:
    current = load_embed_config(db)
    if provider is not None and provider.strip():
        p = provider.strip().lower()
        if p not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported embedding provider: {provider}")
        current.provider = p
        # Switch defaults when flipping provider without explicit model
        if model is None or not str(model).strip():
            if p == "local" and current.model == DEFAULT_REMOTE_MODEL:
                current.model = DEFAULT_LOCAL_MODEL
            elif p == "openai_compatible" and current.model == DEFAULT_LOCAL_MODEL:
                current.model = DEFAULT_REMOTE_MODEL
    if api_key is not None and api_key != "":
        current.api_key = api_key
    if model is not None and model.strip():
        current.model = model.strip()
    if base_url is not None and base_url.strip():
        current.base_url = base_url.strip().rstrip("/")
    payload = json.dumps(current.to_storage())
    row = db.query(SystemSetting).filter(SystemSetting.key == EMBED_SETTING_KEY).one_or_none()
    if row is None:
        db.add(SystemSetting(key=EMBED_SETTING_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    return current


def _get_fastembed_model(model_name: str) -> Any:
    if model_name in _fastembed_cache:
        return _fastembed_cache[model_name]
    from fastembed import TextEmbedding

    logger.info("fastembed_load model=%s", model_name)
    emb = TextEmbedding(model_name=model_name)
    _fastembed_cache[model_name] = emb
    return emb


def _embed_local(texts: list[str], model_name: str) -> tuple[list[list[float]], str]:
    try:
        model = _get_fastembed_model(model_name)
        # FastEmbed yields numpy arrays / lists
        vectors = [list(map(float, vec)) for vec in model.embed(texts)]
        if len(vectors) != len(texts) or not all(vectors):
            logger.warning("fastembed_bad_shape n_in=%s n_out=%s", len(texts), len(vectors))
            return [lexical_vector(t) for t in texts], "lexical"
        logger.info(
            "embed_ok provider=local model=%s n=%s dims=%s",
            model_name,
            len(vectors),
            len(vectors[0]),
        )
        return vectors, "fastembed"
    except Exception as exc:  # noqa: BLE001
        logger.warning("fastembed_fail model=%s err=%s", model_name, exc)
        return [lexical_vector(t) for t in texts], "lexical"


def _embeddings_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/embeddings"):
        return base
    if base.endswith("/v1"):
        return f"{base}/embeddings"
    return f"{base}/v1/embeddings"


def _embed_remote_sync(cfg: EmbeddingConfig, cleaned: list[str], *, timeout: float = 60.0) -> tuple[list[list[float]], str]:
    if not (cfg.api_key and cfg.model and cfg.base_url):
        return [lexical_vector(t) for t in cleaned], "lexical"
    url = _embeddings_url(cfg.base_url)
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": cfg.model, "input": cleaned}
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                logger.warning(
                    "embed_fail status=%s detail=%s",
                    response.status_code,
                    response.text[:300],
                )
                return [lexical_vector(t) for t in cleaned], "lexical"
            data = response.json()
        items = sorted(data.get("data") or [], key=lambda x: int(x.get("index", 0)))
        vectors = [list(map(float, item.get("embedding") or [])) for item in items]
        if len(vectors) != len(cleaned) or not all(vectors):
            return [lexical_vector(t) for t in cleaned], "lexical"
        logger.info("embed_ok provider=openai model=%s n=%s dims=%s", cfg.model, len(vectors), len(vectors[0]))
        return vectors, "openai"
    except Exception as exc:  # noqa: BLE001
        logger.warning("embed_exception err=%s", exc)
        return [lexical_vector(t) for t in cleaned], "lexical"


async def embed_texts(db: Session, texts: list[str], *, timeout: float = 60.0) -> tuple[list[list[float]], str]:
    """Return (vectors, mode) where mode is fastembed|openai|lexical."""
    cleaned = [t.strip() for t in texts if t and str(t).strip()]
    if not cleaned:
        return [], "lexical"
    cfg = load_embed_config(db)
    if cfg.provider == "local":
        if not _fastembed_available():
            logger.warning("fastembed_not_installed fallback=lexical")
            return [lexical_vector(t) for t in cleaned], "lexical"
        return _embed_local(cleaned, cfg.model or DEFAULT_LOCAL_MODEL)
    # openai_compatible — prefer sync httpx off the event loop via to_thread if needed
    return _embed_remote_sync(cfg, cleaned, timeout=timeout)


def embed_texts_sync(db: Session, texts: list[str]) -> tuple[list[list[float]], str]:
    """Sync wrapper for indexing / retrieve paths."""
    cleaned = [t.strip() for t in texts if t and str(t).strip()]
    if not cleaned:
        return [], "lexical"
    cfg = load_embed_config(db)
    if cfg.provider == "local":
        if not _fastembed_available():
            return [lexical_vector(t) for t in cleaned], "lexical"
        return _embed_local(cleaned, cfg.model or DEFAULT_LOCAL_MODEL)
    return _embed_remote_sync(cfg, cleaned)


_TOKEN_RE = re.compile(r"[a-z0-9\u4e00-\u9fff]{2,}", re.I)


def lexical_vector(text: str, *, dims: int = 256) -> list[float]:
    """Deterministic bag-of-hash vector for lexical fallback RAG."""
    vec = [0.0] * dims
    tokens = _TOKEN_RE.findall((text or "").lower())
    if not tokens:
        return vec
    for tok in tokens:
        h = hash(tok) % dims
        vec[h] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(a[i] * a[i] for i in range(n))) or 1.0
    nb = math.sqrt(sum(b[i] * b[i] for i in range(n))) or 1.0
    return dot / (na * nb)


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def lexical_overlap_score(query: str, doc: str) -> float:
    q = tokenize(query)
    d = tokenize(doc)
    if not q or not d:
        return 0.0
    return len(q & d) / max(len(q), 1)
