"""HTTP client / proxy to aulos-knowledge professional plane."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from aulos_api.config import get_settings

logger = logging.getLogger("aulos_api.knowledge_proxy")


def knowledge_base_url() -> str:
    settings = get_settings()
    return (getattr(settings, "knowledge_base_url", None) or "http://127.0.0.1:5095").rstrip("/")


def knowledge_enabled() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "knowledge_plane_enabled", False))


async def proxy_knowledge(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> tuple[int, Any, dict[str, str]]:
    """Returns (status, body, headers). body is dict for JSON or bytes for binary."""
    url = f"{knowledge_base_url()}{path}"
    headers: dict[str, str] = {}
    token = (get_settings().knowledge_admin_token or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(
                method.upper(),
                url,
                json=json_body,
                params=params,
                headers=headers,
            )
            ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
            out_headers = {"content-type": ctype} if ctype else {}
            if ctype.startswith("image/") or ctype.startswith("audio/") or ctype == "application/octet-stream":
                return resp.status_code, resp.content, out_headers
            try:
                data = resp.json()
            except Exception:  # noqa: BLE001
                data = {"detail": resp.text[:500]}
            return resp.status_code, data, {"content-type": "application/json"}
    except httpx.HTTPError as exc:
        logger.warning("knowledge_proxy_error path=%s err=%s", path, exc)
        return 503, {"detail": f"knowledge service unreachable: {exc}"}, {"content-type": "application/json"}


def retrieve_sync(
    *,
    query: str,
    work_id: str = "",
    composer_id: str = "",
    k: int = 6,
) -> dict[str, Any]:
    """Sync retrieve for listening_guide injection."""
    if not knowledge_enabled():
        return {}
    url = f"{knowledge_base_url()}/v1/kb/retrieve"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                url,
                json={"query": query, "work_id": work_id, "composer_id": composer_id, "k": k},
            )
            if resp.status_code >= 400:
                logger.warning("knowledge_retrieve_http status=%s", resp.status_code)
                return {}
            return resp.json()
    except httpx.HTTPError as exc:
        logger.warning("knowledge_retrieve_failed err=%s", exc)
        return {}
