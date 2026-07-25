"""Public media endpoints — cached / proxied ambient audio."""

from __future__ import annotations

import logging
from urllib.parse import unquote

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse

from aulos_api.services.media_cache import (
    content_type_for,
    ensure_cached,
    find_cached,
    validate_source_url,
)

logger = logging.getLogger("aulos_api.media")

router = APIRouter(prefix="/v1/media", tags=["media"])


@router.api_route("/audio", methods=["GET", "HEAD"])
async def media_audio(
    request: Request,
    src: str = Query(min_length=8, max_length=2000),
    mode: str = Query(default="cache"),
):
    """Serve allowlisted remote audio via local cache or reverse-proxy stream."""
    mode = (mode or "cache").strip().lower()
    if mode not in {"cache", "proxy"}:
        mode = "cache"
    try:
        url = validate_source_url(unquote(src.strip()))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if mode == "cache":
        path = find_cached(url) or ensure_cached(url)
        if path is not None:
            # Inline disposition is required — browsers refuse <audio> with attachment.
            return FileResponse(
                path,
                media_type=content_type_for(path),
                content_disposition_type="inline",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "X-Aulos-Media-Mode": "cache",
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": "inline",
                },
            )
        # Cache warm failed — fall through to live proxy.

    if request.method == "HEAD":
        # Lightweight existence probe for proxy mode without pulling the body.
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as probe:
                head = await probe.head(url, headers={"User-Agent": "AulosMediaProxy/0.1"})
                if head.status_code >= 400:
                    get = await probe.get(url, headers={"User-Agent": "AulosMediaProxy/0.1"})
                    status_code = get.status_code
                    ctype = get.headers.get("content-type") or "audio/ogg"
                    clen = get.headers.get("content-length")
                else:
                    status_code = head.status_code
                    ctype = head.headers.get("content-type") or "audio/ogg"
                    clen = head.headers.get("content-length")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail="upstream media unavailable") from exc
        headers = {
            "Cache-Control": "public, max-age=300",
            "X-Aulos-Media-Mode": "proxy",
            "Accept-Ranges": "bytes",
            "Content-Type": ctype,
        }
        if clen:
            headers["Content-Length"] = clen
        return StreamingResponse(iter(()), status_code=status_code, media_type=ctype, headers=headers)

    headers = {"User-Agent": "AulosMediaProxy/0.1 (+https://aulos.purezen.ai)"}
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
    try:
        req = client.build_request("GET", url, headers=headers)
        upstream = await client.send(req, stream=True)
    except Exception as exc:  # noqa: BLE001
        await client.aclose()
        logger.warning("media_proxy_connect_failed url=%s err=%s", url, exc)
        raise HTTPException(status_code=502, detail="upstream media unavailable") from exc

    if upstream.status_code >= 400:
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"upstream status {upstream.status_code}")

    media_type = upstream.headers.get("content-type") or "audio/ogg"
    out_headers = {
        "Cache-Control": "public, max-age=300",
        "X-Aulos-Media-Mode": "proxy",
        "Accept-Ranges": upstream.headers.get("accept-ranges") or "bytes",
    }
    if upstream.headers.get("content-length"):
        out_headers["Content-Length"] = upstream.headers["content-length"]
    if upstream.headers.get("content-range"):
        out_headers["Content-Range"] = upstream.headers["content-range"]

    async def body():
        try:
            async for chunk in upstream.aiter_bytes(64 * 1024):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    # Opportunistically warm disk cache for full-body GETs
    if not range_header and find_cached(url) is None:
        import threading

        threading.Thread(target=ensure_cached, args=(url,), daemon=True).start()

    return StreamingResponse(
        body(),
        status_code=upstream.status_code,
        media_type=media_type,
        headers=out_headers,
    )
