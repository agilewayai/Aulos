"""Listening guide API — classical art-agent MVP + public share + recompose."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import get_current_user
from aulos_api.db.models import ListeningGuide, User
from aulos_api.db.session import get_db
from aulos_api.services.knowledge_base import knowledge_stats, retrieve as kb_retrieve
from aulos_api.services.listening_guide import (
    get_owned_guide,
    get_owned_guide_by_share_slug,
    get_published_guide_by_slug,
    guide_to_dict,
    iter_listening_guide_events,
    iter_recompose_events,
    publish_guide,
    run_listening_guide_workflow,
    unpublish_guide,
    update_publish_guide,
)
from aulos_api.timefmt import to_utc_iso_optional

router = APIRouter(tags=["listening-guides"])
private = APIRouter(prefix="/v1/listening-guides", tags=["listening-guides"])
public = APIRouter(prefix="/v1/public/guides", tags=["public-guides"])
knowledge = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])


_MOBILE_CSS_PATCH = """
<style id="aulos-mobile-harden">
img{max-width:100%;height:auto}
.portrait{width:100%}
.portrait img{width:100%;height:auto;display:block;background:#1a1510}
@media(max-width:719px){
  .wrap{padding:1.35rem 1rem 3.25rem!important}
  .portrait{max-width:17rem;margin:0 auto}
  .portrait img{max-height:min(68vh,26rem);object-fit:contain;object-position:top center}
  h1{font-size:clamp(1.75rem,7vw,2.4rem)!important}
}
</style>
"""

# Serve-time only: public share pages stay clean without recompose.
_SHARE_CHROME_PATCH = """
<style id="aulos-share-chrome">
#aulos-owner-bar{display:none!important}
body.has-owner-bar{padding-top:0!important}
.wrap{padding-bottom:7.5rem!important}
.ambient{position:fixed!important;z-index:60!important;right:0.75rem!important;bottom:0.75rem!important;left:auto!important;width:min(22.5rem,calc(100vw - 1.5rem))!important;margin:0!important;padding:0.35rem 0.5rem!important;border:1px solid rgba(232,239,233,0.11)!important;background:rgba(16,22,27,0.92)!important;backdrop-filter:blur(12px);box-shadow:0 12px 36px rgba(0,0,0,0.45);max-height:min(72vh,30rem)!important;display:flex!important;flex-direction:column!important}
.ambient .ambient-mini{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:0.4rem;align-items:center;flex:0 0 auto}
.ambient.is-collapsed .ambient-details,
.ambient.is-collapsed .ambient-credit,
.ambient.is-collapsed .ambient-hint,
.ambient.is-collapsed .ambient-kicker{display:none!important}
.ambient .ambient-toggle{width:1.7rem!important;height:1.7rem!important;border-radius:999px;padding:0!important;min-height:0!important;display:inline-flex;align-items:center;justify-content:center;font-size:0!important}
.ambient .ambient-title{margin:0!important;font-size:0.72rem!important;line-height:1.25!important;font-weight:500!important;color:#9aafa3!important;font-family:Manrope,system-ui,sans-serif!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ambient:not(.is-collapsed) .ambient-title{white-space:normal;color:#e8efe9!important;font-size:0.88rem!important;font-family:Fraunces,"Noto Serif SC",serif!important}
.ambient .ambient-expand{appearance:none;border:0;background:transparent;color:#9aafa3;font:inherit;font-size:0.62rem!important;cursor:pointer;text-decoration:underline;text-underline-offset:0.12em;white-space:nowrap;opacity:0.85;padding:0.1rem 0!important}
.ambient .ambient-expand:hover{color:#c9a66b;opacity:1}
.ambient .ambient-details{padding:0.1rem 0;border-top:1px solid rgba(232,239,233,0.11);margin-top:0.4rem;overflow:auto;flex:1 1 auto;min-height:0}
.ambient .ambient-credit,.ambient .ambient-hint{margin:0.4rem 0 0!important;font-size:0.72rem!important}
.ambient audio{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;overflow:hidden;clip:rect(0 0 0 0)}
.lang-switch{display:inline-flex!important;gap:0.15rem!important;margin:0 0 0.85rem!important;padding:0.12rem!important;border:1px solid rgba(232,239,233,0.11)!important;background:rgba(21,28,34,0.7)!important}
.lang-switch button{font-size:0.68rem!important;font-weight:600!important;padding:0.22rem 0.5rem!important;min-height:0!important;line-height:1.2!important;letter-spacing:0.02em!important}
@media (max-width:719px){.ambient{right:0.5rem!important;left:0.5rem!important;bottom:0.5rem!important;width:auto!important;max-height:min(60vh,24rem)!important}.wrap{padding-bottom:6.5rem!important}}
</style>
<script id="aulos-share-chrome-js">
(function () {
  function wipeOwnerChrome() {
    var bar = document.getElementById("aulos-owner-bar");
    if (bar) bar.remove();
    document.body.classList.remove("has-owner-bar");
    document.querySelectorAll("script").forEach(function (s) {
      var t = s.textContent || "";
      if (t.indexOf("aulos-owner-bar") >= 0 && s.id !== "aulos-share-chrome-js") s.remove();
    });
  }
  function compactAmbient() {
    var amb = document.querySelector(".ambient");
    if (!amb) return;
    wipeOwnerChrome();
    if (amb.querySelector(".ambient-mini")) {
      amb.classList.add("is-collapsed");
      return;
    }
    var title = amb.querySelector(".ambient-title");
    var kicker = amb.querySelector(".ambient-kicker");
    var credit = amb.querySelector(".ambient-credit");
    var hint = amb.querySelector(".ambient-hint");
    var toggle = amb.querySelector(".ambient-toggle");
    var audio = amb.querySelector("audio");
    var lang = (document.documentElement.getAttribute("lang") || "").indexOf("zh") === 0 ? "zh" : "en";
    var expandLabel = lang === "zh" ? "说明" : "Info";
    var collapseLabel = lang === "zh" ? "收起" : "Hide";
    var mini = document.createElement("div");
    mini.className = "ambient-mini";
    var text = document.createElement("div");
    text.className = "ambient-mini-text";
    if (kicker) text.appendChild(kicker);
    if (title) text.appendChild(title);
    var expand = document.createElement("button");
    expand.type = "button";
    expand.className = "ambient-expand";
    expand.setAttribute("aria-expanded", "false");
    expand.textContent = expandLabel;
    if (toggle) mini.appendChild(toggle);
    mini.appendChild(text);
    mini.appendChild(expand);
    var details = document.createElement("div");
    details.className = "ambient-details";
    details.hidden = true;
    if (credit) details.appendChild(credit);
    if (hint) details.appendChild(hint);
    amb.innerHTML = "";
    amb.appendChild(mini);
    amb.appendChild(details);
    if (audio) amb.appendChild(audio);
    amb.classList.add("is-collapsed");
    expand.addEventListener("click", function () {
      var open = amb.classList.toggle("is-collapsed") === false;
      open = !amb.classList.contains("is-collapsed");
      details.hidden = !open;
      expand.setAttribute("aria-expanded", open ? "true" : "false");
      expand.textContent = open ? collapseLabel : expandLabel;
    });
  }
  wipeOwnerChrome();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", compactAmbient);
  } else {
    compactAmbient();
  }
  // Owner script may race-create the bar later
  setTimeout(wipeOwnerChrome, 0);
  setTimeout(wipeOwnerChrome, 400);
})();
</script>
<script id="aulos-ambient-failover">
(function () {
  function encodeSrc(u) {
    try { return encodeURIComponent(u); } catch (e) { return ""; }
  }
  function resolveUrl(u) {
    if (!u) return u;
    if (/^(https?:|blob:|data:)/i.test(u)) return u;
    try { return new URL(u, document.baseURI || window.location.href).href; } catch (e) { return u; }
  }
  function wire(ambient) {
    if (!ambient || ambient.getAttribute("data-failover-wired") === "1") return;
    if (ambient.getAttribute("data-ambient-player") === "v2") return;
    var audio = ambient.querySelector("audio") || document.getElementById("aulos-ambient");
    if (!audio) return;
    var origin = ambient.getAttribute("data-origin-src") || "";
    if (!origin) {
      var s = audio.querySelector("source");
      origin = (s && s.getAttribute("src")) || audio.getAttribute("src") || "";
    }
    if (!origin || origin.indexOf("/v1/media/") === 0) return;
    if (origin.indexOf("http") !== 0) return;
    ambient.setAttribute("data-failover-wired", "1");
    if (!ambient.getAttribute("data-origin-src")) ambient.setAttribute("data-origin-src", origin);
    if (!ambient.getAttribute("data-cache-src")) {
      ambient.setAttribute("data-cache-src", "/v1/media/audio?src=" + encodeSrc(origin) + "&mode=cache");
    }
    if (!ambient.getAttribute("data-proxy-src")) {
      ambient.setAttribute("data-proxy-src", "/v1/media/audio?src=" + encodeSrc(origin) + "&mode=proxy");
    }
    if (ambient.getAttribute("data-ambient-failover-ready") === "1") return;
    // If the page already ships the new player script, skip duplicate wiring.
    if (audio.getAttribute("data-active-tier")) {
      ambient.setAttribute("data-ambient-failover-ready", "1");
      return;
    }
    var originSrc = ambient.getAttribute("data-origin-src");
    var cacheSrc = ambient.getAttribute("data-cache-src");
    var proxySrc = ambient.getAttribute("data-proxy-src");
    var tiers = ["cache", "proxy", "origin"];
    var idx = 0;
    var key = "aulos_ambient_tier:" + originSrc;
    try {
      var saved = localStorage.getItem(key);
      if (saved === "proxy") idx = 1;
      else if (saved === "origin") idx = 2;
      else idx = 0;
    } catch (e) {}
    var stallTimer = null;
    var busy = false;
    function urlFor(i) {
      if (tiers[i] === "cache") return cacheSrc;
      if (tiers[i] === "proxy") return proxySrc;
      return originSrc;
    }
    function apply(i) {
      idx = i;
      var src = resolveUrl(urlFor(idx));
      if (!src) return;
      while (audio.firstChild) audio.removeChild(audio.firstChild);
      audio.removeAttribute("src");
      audio.src = src;
      audio.setAttribute("data-active-tier", tiers[idx]);
      try { audio.load(); } catch (e) {}
    }
    function remember() {
      try { localStorage.setItem(key, tiers[idx]); } catch (e) {}
    }
    function clearStall() {
      if (stallTimer) { clearTimeout(stallTimer); stallTimer = null; }
    }
    function watch() {
      clearStall();
      var last = audio.currentTime || 0;
      stallTimer = setTimeout(function () {
        if (!audio.paused && (audio.currentTime || 0) <= last + 0.05 && !audio.ended) failover("stall");
      }, 4500);
    }
    function failover(reason) {
      if (busy || idx >= tiers.length - 1) return;
      busy = true;
      clearStall();
      var playing = !audio.paused;
      var t = audio.currentTime || 0;
      apply(idx + 1);
      remember();
      audio.addEventListener("loadedmetadata", function onMeta() {
        audio.removeEventListener("loadedmetadata", onMeta);
        try { if (t > 0 && isFinite(t)) audio.currentTime = t; } catch (e) {}
        busy = false;
        if (playing) {
          var p = audio.play();
          if (p && p.catch) p.catch(function () {});
        }
      });
      setTimeout(function () { busy = false; }, 1200);
    }
    apply(idx);
    audio.addEventListener("error", function () { failover("error"); });
    audio.addEventListener("stalled", function () { failover("stalled"); });
    audio.addEventListener("waiting", watch);
    audio.addEventListener("playing", function () { remember(); clearStall(); watch(); });
    audio.addEventListener("play", watch);
    audio.addEventListener("pause", clearStall);
    ambient.setAttribute("data-ambient-failover-ready", "1");
  }
  function boot() {
    document.querySelectorAll(".ambient").forEach(wire);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
  setTimeout(boot, 300);
})();
</script>
"""


def _public_harden_guide_html(html: str) -> str:
    """Patch stored public guides at serve time — no recompose needed for chrome/style."""
    out = html.replace('loading="lazy"', 'loading="eager"')
    if "referrerpolicy=" not in out and "<img " in out:
        out = out.replace(
            "<img ",
            '<img decoding="async" fetchpriority="high" referrerpolicy="no-referrer" ',
            1,
        )
    if "aulos-mobile-harden" not in out and "</head>" in out:
        out = out.replace("</head>", _MOBILE_CSS_PATCH + "</head>", 1)
    if "aulos-share-chrome" not in out and "</body>" in out:
        out = out.replace("</body>", _SHARE_CHROME_PATCH + "</body>", 1)
    elif "aulos-share-chrome" not in out and "</html>" in out:
        out = out.replace("</html>", _SHARE_CHROME_PATCH + "</html>", 1)
    # Float + prefer-cache patch can land on guides that already have an older share-chrome block.
    if "aulos-ambient-float-live" not in out:
        float_patch = (
            '<style id="aulos-ambient-float-live">'
            ".wrap{padding-bottom:7.5rem!important}"
            ".ambient{position:fixed!important;z-index:60!important;right:0.75rem!important;"
            "bottom:0.75rem!important;left:auto!important;"
            "width:min(22.5rem,calc(100vw - 1.5rem))!important;margin:0!important;"
            "max-height:min(72vh,30rem)!important;display:flex!important;flex-direction:column!important;"
            "background:rgba(16,22,27,0.92)!important;backdrop-filter:blur(12px);"
            "box-shadow:0 12px 36px rgba(0,0,0,0.45)}"
            ".ambient .ambient-details{overflow:auto;flex:1 1 auto;min-height:0}"
            "@media (max-width:719px){.ambient{right:0.5rem!important;left:0.5rem!important;"
            "bottom:0.5rem!important;width:auto!important;max-height:min(60vh,24rem)!important}"
            ".wrap{padding-bottom:6.5rem!important}}"
            "</style>"
            '<script id="aulos-prefer-cache-live">'
            "(function(){function nudge(){document.querySelectorAll('.ambient[data-cache-src]').forEach(function(amb){"
            "var cache=amb.getAttribute('data-cache-src');var origin=amb.getAttribute('data-origin-src')||'';"
            "if(!cache)return;try{localStorage.setItem('aulos_ambient_tier:'+origin,'cache');}catch(e){}"
            "var audio=amb.querySelector('audio');if(!audio||!audio.paused)return;"
            "var tier=audio.getAttribute('data-active-tier');if(tier==='cache'||tier==='proxy')return;"
            "try{audio.src=new URL(cache,location.href).href;audio.setAttribute('data-active-tier','cache');audio.load();}catch(e){}"
            "});}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(nudge,50);});"
            "else setTimeout(nudge,50);setTimeout(nudge,400);})();"
            "</script>"
        )
        if "</body>" in out:
            out = out.replace("</body>", float_patch + "</body>", 1)
        elif "</html>" in out:
            out = out.replace("</html>", float_patch + "</html>", 1)
    return out


def _mobile_harden_guide_html(html: str) -> str:
    """Backward-compatible alias."""
    return _public_harden_guide_html(html)


class ListeningGuideRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    work_hint: str | None = Field(default=None, max_length=255)


class RecomposeRequest(BaseModel):
    message: str | None = Field(default=None, max_length=2000)
    work_hint: str | None = Field(default=None, max_length=255)


class WorkflowStepOut(BaseModel):
    id: str
    title: str
    status: str
    thinking: str = ""
    detail: str = ""
    skill_id: str | None = None
    skill_version: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


class ListeningGuideOut(BaseModel):
    id: int
    work_title: str
    composer: str
    status: str
    source: str
    summary: str
    guide_html: str
    steps: list[WorkflowStepOut]
    skill_versions: dict[str, str] = {}
    eval_pass: bool | None = None
    eval_score: int | None = None
    created_at: datetime | str | None = None
    published: bool = False
    share_slug: str | None = None
    share_path: str | None = None
    published_at: datetime | str | None = None


class PublicGuideMeta(BaseModel):
    work_title: str
    composer: str
    summary: str
    share_slug: str
    share_path: str
    published_at: datetime | str | None = None


class ShareOwnershipOut(BaseModel):
    id: int
    work_title: str
    composer: str
    published: bool
    share_slug: str | None = None
    share_path: str | None = None
    owner: bool = True


def _sse(event_iter):
    async def event_gen():
        async for item in event_iter:
            event = item.get("event", "message")
            data = json.dumps(item.get("data") or {}, ensure_ascii=False)
            yield f"event: {event}\ndata: {data}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@private.post("", response_model=ListeningGuideOut, status_code=status.HTTP_201_CREATED)
async def create_listening_guide(
    body: ListeningGuideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = await run_listening_guide_workflow(
        db=db,
        user_id=user.id,
        message=body.message.strip(),
        work_hint=(body.work_hint or "").strip() or None,
    )
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/stream")
async def stream_listening_guide(
    body: ListeningGuideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    return _sse(
        iter_listening_guide_events(
            db=db,
            user_id=user.id,
            message=body.message.strip(),
            work_hint=(body.work_hint or "").strip() or None,
        )
    )


@private.get("", response_model=list[ListeningGuideOut])
def list_listening_guides(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ListeningGuideOut]:
    rows = (
        db.query(ListeningGuide)
        .filter(ListeningGuide.user_id == user.id)
        .order_by(ListeningGuide.id.desc())
        .limit(20)
        .all()
    )
    return [ListeningGuideOut(**guide_to_dict(r)) for r in rows]


@private.get("/by-share/{slug}", response_model=ShareOwnershipOut)
def get_guide_by_share_slug(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareOwnershipOut:
    row = get_owned_guide_by_share_slug(db, user_id=user.id, slug=slug)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found for this account")
    published = bool(row.share_slug and row.published_at)
    return ShareOwnershipOut(
        id=row.id,
        work_title=row.work_title,
        composer=row.composer or "",
        published=published,
        share_slug=row.share_slug if published else row.share_slug,
        share_path=f"/g/{row.share_slug}" if row.share_slug else None,
        owner=True,
    )


@private.get("/{guide_id}", response_model=ListeningGuideOut)
def get_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = get_owned_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/{guide_id}/recompose/stream")
async def stream_recompose_guide(
    guide_id: int,
    body: RecomposeRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    body = body or RecomposeRequest()
    row = get_owned_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return _sse(
        iter_recompose_events(
            db=db,
            user_id=user.id,
            guide_id=guide_id,
            message=(body.message or "").strip() or None,
            work_hint=(body.work_hint or "").strip() or None,
        )
    )


@private.post("/{guide_id}/update-publish", response_model=ListeningGuideOut)
def update_publish_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = update_publish_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/{guide_id}/publish", response_model=ListeningGuideOut)
def publish_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = publish_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/{guide_id}/unpublish", response_model=ListeningGuideOut)
def unpublish_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = unpublish_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@public.get("/{slug}", response_class=HTMLResponse)
def public_guide_page(slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Public share page — no authentication. Serves the composed guide HTML only."""
    row = get_published_guide_by_slug(db, slug)
    if row is None or not (row.guide_html or "").strip():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared guide not found")
    html = _mobile_harden_guide_html(row.guide_html)
    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "public, max-age=60",
            "X-Robots-Tag": "noindex",
        },
    )


@public.get("/{slug}/meta", response_model=PublicGuideMeta)
def public_guide_meta(slug: str, db: Session = Depends(get_db)) -> PublicGuideMeta:
    row = get_published_guide_by_slug(db, slug)
    if row is None or not row.share_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared guide not found")
    return PublicGuideMeta(
        work_title=row.work_title,
        composer=row.composer or "",
        summary=row.summary or "",
        share_slug=row.share_slug,
        share_path=f"/g/{row.share_slug}",
        published_at=to_utc_iso_optional(row.published_at),
    )


@knowledge.get("/search")
def knowledge_search(
    q: str = Query(min_length=1, max_length=500),
    work_hint: str = Query(default="", max_length=255),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = kb_retrieve(
        db,
        query=q,
        work_hint=work_hint,
        user_id=user.id,
        k=6,
    )
    # Don't dump full dossier in search preview
    dossier = result.get("kb_dossier") or {}
    return {
        "rag_mode": result.get("rag_mode"),
        "hits": result.get("hits") or [],
        "matched_title": dossier.get("work_title"),
        "matched_composer": dossier.get("composer"),
        "stats": knowledge_stats(db),
    }


@knowledge.get("/stats")
def get_knowledge_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return knowledge_stats(db)


router.include_router(private)
router.include_router(public)
router.include_router(knowledge)
