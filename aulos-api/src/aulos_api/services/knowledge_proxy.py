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


def fetch_composer_dossier_sync(composer_id: str) -> dict[str, Any]:
    """Sync GET composer dossier for listening thicken (SPEC-025)."""
    cid = (composer_id or "").strip()
    if not cid or not knowledge_enabled():
        return {}
    url = f"{knowledge_base_url()}/v1/kb/composers/{cid}/dossier"
    headers: dict[str, str] = {}
    token = (get_settings().knowledge_admin_token or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code >= 400:
                logger.warning(
                    "knowledge_dossier_http composer=%s status=%s", cid, resp.status_code
                )
                return {}
            data = resp.json()
            return data if isinstance(data, dict) else {}
    except httpx.HTTPError as exc:
        logger.warning("knowledge_dossier_failed composer=%s err=%s", cid, exc)
        return {}


def dossier_is_thin(dossier: dict[str, Any] | None) -> bool:
    """True when knowledge-plane composer dossier cannot thicken Salon craft."""
    from aulos_skills.knowledge_thicken import dossier_is_thin as _thin

    return _thin(dossier)


def enqueue_composer_dossier_build_sync(composer_id: str) -> dict[str, Any]:
    """Fire-and-forget POST build-dossier (SPEC-026). Never blocks compose on crawl."""
    cid = (composer_id or "").strip()
    if not cid or not knowledge_enabled():
        return {}
    url = f"{knowledge_base_url()}/v1/admin/composers/{cid}/build-dossier"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = (get_settings().knowledge_admin_token or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json={"async_mode": True})
            if resp.status_code >= 400:
                logger.warning(
                    "knowledge_dossier_enqueue_http composer=%s status=%s body=%s",
                    cid,
                    resp.status_code,
                    (resp.text or "")[:200],
                )
                return {"ok": False, "status": resp.status_code, "composer_id": cid}
            data = resp.json() if resp.content else {}
            logger.info(
                "knowledge_dossier_enqueued composer=%s job=%s status=%s",
                cid,
                (data or {}).get("job_id"),
                (data or {}).get("status"),
            )
            return {"ok": True, "composer_id": cid, **(data if isinstance(data, dict) else {})}
    except httpx.HTTPError as exc:
        logger.warning("knowledge_dossier_enqueue_failed composer=%s err=%s", cid, exc)
        return {"ok": False, "composer_id": cid, "error": str(exc)}


def ensure_catalog_composer_dossiers(*, dry_run: bool = False) -> dict[str, Any]:
    """Enqueue build-dossier for every Catalog composer with a thin knowledge dossier."""
    try:
        from aulos_skills.identity import load_catalog
    except ImportError:
        return {"ok": False, "error": "aulos_skills unavailable", "rich": [], "enqueued": [], "failed": []}

    if not knowledge_enabled() and not dry_run:
        return {
            "ok": False,
            "error": "knowledge plane disabled",
            "dry_run": dry_run,
            "rich": [],
            "enqueued": [],
            "failed": [],
        }

    load_catalog.cache_clear()
    cat = load_catalog()
    rich: list[str] = []
    enqueued: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for cid in sorted(cat.composers.keys()):
        dossier = fetch_composer_dossier_sync(cid) if knowledge_enabled() else {}
        if not dossier_is_thin(dossier):
            rich.append(cid)
            continue
        if dry_run:
            enqueued.append({"composer_id": cid, "dry_run": True, "ok": True})
            continue
        result = enqueue_composer_dossier_build_sync(cid)
        if result.get("ok"):
            enqueued.append(result)
        else:
            failed.append(result or {"composer_id": cid, "ok": False})
    return {
        "ok": not failed,
        "dry_run": dry_run,
        "rich": rich,
        "enqueued": enqueued,
        "failed": failed,
        "composer_count": len(cat.composers),
    }
