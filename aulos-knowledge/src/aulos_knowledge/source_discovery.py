"""REQ-009 — Authority source discovery via depth+breadth graph search."""

from __future__ import annotations

import json
import logging
import re
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from aulos_knowledge.connectors import connector_registered
from aulos_knowledge.db import ComposerEntity, SourceAuthority, SourceDiscoveryRun, WorkEntity, utcnow
from aulos_knowledge.fetch_policy import assert_url_allowed, throttle
from aulos_knowledge.jobs import enqueue_and_maybe_run as enqueue_fetch_job
from aulos_knowledge.registry import load_registry_manifest

logger = logging.getLogger("aulos_knowledge.source_discovery")

UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; source-discovery)"

# Wikidata properties that surface authority URLs or resolvable IDs
URL_CLAIM_PROPS = ("P856", "P973", "P1343")
EXTERNAL_ID_PROPS: dict[str, Callable[[str], str]] = {
    "P434": lambda v: f"https://musicbrainz.org/artist/{v}",
    "P839": lambda v: f"https://imslp.org/wiki/{v.replace(' ', '_')}",
}

# Lateral authority neighborhoods (breadth expansion from registry nodes)
AUTHORITY_NEIGHBORS: dict[str, list[dict[str, str]]] = {
    "wikidata": [
        {"id": "wikipedia", "relation": "sibling_encyclopedia"},
        {"id": "commons", "label": "Wikimedia Commons", "url": "https://commons.wikimedia.org/", "relation": "sibling_media"},
    ],
    "wikipedia": [
        {"id": "wikidata", "relation": "structured_data"},
    ],
    "musicbrainz": [
        {"id": "coverartarchive", "label": "Cover Art Archive", "url": "https://coverartarchive.org/", "relation": "media_archive"},
    ],
    "imslp": [
        {"id": "wikimedia-scores", "label": "IMSLP (Wikimedia)", "url": "https://imslp.org/", "relation": "score_library"},
    ],
    "rism": [
        {"id": "viaf", "label": "VIAF", "url": "https://viaf.org/", "relation": "authority_file"},
        {"id": "loc", "label": "Library of Congress", "url": "https://id.loc.gov/", "relation": "authority_file"},
    ],
}

# Domain → suggested tier / origin for scoring
DOMAIN_AUTHORITY_HINTS: dict[str, dict[str, Any]] = {
    "wikidata.org": {"tier": "S", "origin_class": "encyclopedia", "score": 40},
    "wikipedia.org": {"tier": "A", "origin_class": "encyclopedia", "score": 35},
    "musicbrainz.org": {"tier": "S", "origin_class": "encyclopedia", "score": 40},
    "imslp.org": {"tier": "A", "origin_class": "media", "score": 35},
    "rism.online": {"tier": "A", "origin_class": "encyclopedia", "score": 35},
    "viaf.org": {"tier": "A", "origin_class": "encyclopedia", "score": 30},
    "loc.gov": {"tier": "A", "origin_class": "encyclopedia", "score": 30},
    "worldcat.org": {"tier": "B", "origin_class": "encyclopedia", "score": 20},
    "britannica.com": {"tier": "A", "origin_class": "encyclopedia", "score": 25},
    "oxfordmusiconline.com": {"tier": "S", "origin_class": "encyclopedia", "score": 30},
    "bach-cantatas.com": {"tier": "B", "origin_class": "editorial", "score": 15},
    "allmusic.com": {"tier": "B", "origin_class": "editorial", "score": 10},
}

BLOCKED_DOMAIN_FRAGMENTS = (
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "spotify.com",
    "youtube.com",
    "reddit.com",
)


@dataclass
class GraphNode:
    id: str
    kind: str  # registry_source | entity | url | candidate
    label: str = ""
    url: str = ""
    depth: int = 0
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    src: str
    dst: str
    relation: str


def _domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _domain_slug(url: str) -> str:
    host = _domain(url)
    parts = host.split(".")
    base = parts[-2] if len(parts) >= 2 else parts[0]
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "source"


def _claim_string(claim: dict[str, Any]) -> str:
    snak = (claim or {}).get("mainsnak") or {}
    dv = snak.get("datavalue") or {}
    val = dv.get("value")
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        return str(val.get("id") or val.get("text") or "").strip()
    return ""


def _extract_wikidata_urls(entity: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (url, relation) pairs from entity claims."""
    out: list[tuple[str, str]] = []
    claims = (entity.get("claims") or {}) if isinstance(entity, dict) else {}
    for prop in URL_CLAIM_PROPS:
        for claim in claims.get(prop) or []:
            raw = _claim_string(claim)
            if raw.startswith("http"):
                rel = {"P856": "official_website", "P973": "described_by", "P1343": "described_by"}.get(
                    prop, "reference"
                )
                out.append((raw, rel))
    for prop, resolver in EXTERNAL_ID_PROPS.items():
        for claim in claims.get(prop) or []:
            raw = _claim_string(claim)
            if raw:
                out.append((resolver(raw), f"external_id:{prop}"))
    return out


def _score_url(url: str, relation: str, *, in_registry: bool) -> float:
    if any(b in _domain(url) for b in BLOCKED_DOMAIN_FRAGMENTS):
        return -100.0
    score = 5.0
    host = _domain(url)
    for domain, hint in DOMAIN_AUTHORITY_HINTS.items():
        if host == domain or host.endswith("." + domain):
            score += float(hint.get("score") or 0)
            break
    if relation == "official_website":
        score += 15.0
    elif relation.startswith("described"):
        score += 10.0
    elif relation.startswith("external_id"):
        score += 12.0
    if in_registry:
        score += 50.0
    return score


def _fetch_wikidata_entity(
    qid: str,
    *,
    source: SourceAuthority,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    assert_url_allowed(source, url)
    throttle(source)
    if client is not None:
        resp = client.get(url)
        resp.raise_for_status()
        payload = resp.json()
    else:
        with httpx.Client(timeout=30.0, headers={"User-Agent": UA}) as c:
            resp = c.get(url)
            resp.raise_for_status()
            payload = resp.json()
    entities = (payload.get("entities") or {}) if isinstance(payload, dict) else {}
    return entities.get(qid) or {}


def _registry_index(db: Session) -> dict[str, SourceAuthority]:
    return {r.id: r for r in db.query(SourceAuthority).all()}


def _known_urls(registry: dict[str, SourceAuthority]) -> set[str]:
    urls: set[str] = set()
    for row in registry.values():
        try:
            bases = json.loads(row.base_urls_json or "[]")
        except json.JSONDecodeError:
            bases = []
        for u in bases:
            if u:
                urls.add(str(u).rstrip("/"))
    manifest = load_registry_manifest()
    for entry in list(manifest.get("sources") or []) + list(manifest.get("candidates") or []):
        for u in entry.get("base_urls") or []:
            if u:
                urls.add(str(u).rstrip("/"))
    return urls


def _seed_from_registry(registry: dict[str, SourceAuthority]) -> list[GraphNode]:
    seeds: list[GraphNode] = []
    for sid, row in registry.items():
        if (row.verification_status or "") not in ("verified", "candidate"):
            continue
        seeds.append(
            GraphNode(
                id=f"registry:{sid}",
                kind="registry_source",
                label=row.name or sid,
                url=(json.loads(row.base_urls_json or "[]") or [""])[0],
                depth=0,
                score=80.0 if row.verification_status == "verified" else 40.0,
                metadata={
                    "source_id": sid,
                    "verification_status": row.verification_status,
                    "connector": row.connector,
                },
            )
        )
    return seeds


def _seed_from_composer(db: Session, composer_id: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    row = db.get(ComposerEntity, composer_id)
    if not row:
        return [], []
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    try:
        ext = json.loads(row.external_ids_json or "{}")
    except json.JSONDecodeError:
        ext = {}
    nid = f"entity:composer:{composer_id}"
    nodes.append(
        GraphNode(
            id=nid,
            kind="entity",
            label=row.name_en or composer_id,
            depth=0,
            score=20.0,
            metadata={"composer_id": composer_id, "external_ids": ext},
        )
    )
    qid = str(ext.get("wikidata") or ext.get("wikidata_qid") or "")
    if qid:
        qn = f"entity:wikidata:{qid}"
        nodes.append(GraphNode(id=qn, kind="entity", label=qid, depth=1, score=15.0, metadata={"qid": qid}))
        edges.append(GraphEdge(src=nid, dst=qn, relation="wikidata_id"))
    works = db.query(WorkEntity).filter(WorkEntity.composer_id == composer_id).limit(12).all()
    for w in works:
        wid = f"entity:work:{w.id}"
        nodes.append(
            GraphNode(
                id=wid,
                kind="entity",
                label=w.title_en or w.id,
                depth=1,
                score=10.0,
                metadata={"work_id": w.id, "aulos_work_id": w.aulos_work_id},
            )
        )
        edges.append(GraphEdge(src=nid, dst=wid, relation="composer_work"))
        try:
            wext = json.loads(w.external_ids_json or "{}")
        except json.JSONDecodeError:
            wext = {}
        wq = str(wext.get("wikidata") or "")
        if wq:
            wqn = f"entity:wikidata:{wq}"
            nodes.append(GraphNode(id=wqn, kind="entity", label=wq, depth=2, score=8.0, metadata={"qid": wq}))
            edges.append(GraphEdge(src=wid, dst=wqn, relation="wikidata_id"))
    return nodes, edges


def _source_crawlable(db: Session, source_id: str) -> bool:
    src = db.get(SourceAuthority, source_id)
    if not src:
        return False
    return (
        (src.verification_status or "") == "verified"
        and bool(src.enabled)
        and connector_registered(src.connector or "")
    )


def run_source_discovery(
    db: Session,
    *,
    composer_id: str = "",
    wikidata_qid: str = "",
    max_depth: int = 2,
    max_breadth: int = 24,
    max_nodes: int = 48,
    fetch_wikidata: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Depth+breadth graph search for authority source candidates."""
    registry = _registry_index(db)
    known_urls = _known_urls(registry)
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    seed_hints: dict[str, Any] = {
        "composer_id": composer_id,
        "wikidata_qid": (wikidata_qid or "").upper(),
        "wikipedia_title": "",
        "musicbrainz_id": "",
        "imslp_page": "",
    }

    def add_node(node: GraphNode) -> None:
        prev = nodes.get(node.id)
        if prev is None or node.score > prev.score:
            nodes[node.id] = node

    def add_edge(edge: GraphEdge) -> None:
        edges.append(edge)

    for seed in _seed_from_registry(registry):
        add_node(seed)

    if composer_id:
        c_nodes, c_edges = _seed_from_composer(db, composer_id)
        for n in c_nodes:
            add_node(n)
        edges.extend(c_edges)

    extra_qids: list[str] = []
    if wikidata_qid:
        extra_qids.append(wikidata_qid.upper())
    for n in list(nodes.values()):
        q = str((n.metadata or {}).get("qid") or "")
        if q:
            extra_qids.append(q.upper())
    extra_qids = list(dict.fromkeys(extra_qids))

    wikidata_source = registry.get("wikidata")
    if wikidata_source and extra_qids:
        fetcher = fetch_wikidata
        if fetcher is None:
            client_holder: dict[str, httpx.Client] = {}

            def _default_fetch(qid: str) -> dict[str, Any]:
                if "client" not in client_holder:
                    client_holder["client"] = httpx.Client(timeout=30.0, headers={"User-Agent": UA})
                return _fetch_wikidata_entity(qid, source=wikidata_source, client=client_holder["client"])

            fetcher = _default_fetch
        for qid in extra_qids[:max_breadth]:
            try:
                entity = fetcher(qid)
            except Exception as exc:  # noqa: BLE001
                logger.warning("wikidata_fetch_failed qid=%s err=%s", qid, exc)
                continue
            label = ((entity.get("labels") or {}).get("en") or {}).get("value") or qid
            enid = f"entity:wikidata:{qid}"
            add_node(
                GraphNode(
                    id=enid,
                    kind="entity",
                    label=label,
                    depth=1,
                    score=18.0,
                    metadata={"qid": qid},
                )
            )
            primary = (seed_hints.get("wikidata_qid") or extra_qids[0] or "").upper()
            if qid == primary:
                seed_hints["wikidata_qid"] = qid
                if not seed_hints["wikipedia_title"]:
                    seed_hints["wikipedia_title"] = label
                claims = entity.get("claims") or {}
                for claim in claims.get("P434") or []:
                    mbid = _claim_string(claim)
                    if mbid:
                        seed_hints["musicbrainz_id"] = mbid
                        break
                for claim in claims.get("P839") or []:
                    page = _claim_string(claim)
                    if page:
                        seed_hints["imslp_page"] = page
                        break
            for url, relation in _extract_wikidata_urls(entity):
                uid = f"url:{_domain_slug(url)}"
                in_reg = any(url.rstrip("/").startswith(k) for k in known_urls)
                add_node(
                    GraphNode(
                        id=uid,
                        kind="url",
                        label=_domain(url),
                        url=url,
                        depth=2,
                        score=_score_url(url, relation, in_registry=in_reg),
                        metadata={"relation": relation, "from_qid": qid},
                    )
                )
                add_edge(GraphEdge(src=enid, dst=uid, relation=relation))

    if composer_id and not seed_hints.get("composer_id"):
        seed_hints["composer_id"] = composer_id
    if not seed_hints.get("wikidata_qid") and extra_qids:
        seed_hints["wikidata_qid"] = extra_qids[0]

    # Breadth: lateral registry neighbors + manifest candidates
    breadth_count = 0
    for seed in [n for n in nodes.values() if n.kind == "registry_source"]:
        sid = str((seed.metadata or {}).get("source_id") or "")
        for neighbor in AUTHORITY_NEIGHBORS.get(sid, []):
            if breadth_count >= max_breadth:
                break
            nid = f"neighbor:{neighbor.get('id', '')}"
            url = neighbor.get("url") or ""
            add_node(
                GraphNode(
                    id=nid,
                    kind="candidate",
                    label=neighbor.get("label") or neighbor.get("id", ""),
                    url=url,
                    depth=1,
                    score=22.0,
                    metadata={"relation": neighbor.get("relation", "sibling")},
                )
            )
            add_edge(GraphEdge(src=seed.id, dst=nid, relation=str(neighbor.get("relation") or "sibling")))
            breadth_count += 1

    manifest = load_registry_manifest()
    for entry in manifest.get("candidates") or []:
        if breadth_count >= max_breadth:
            break
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("id") or "")
        bases = entry.get("base_urls") or []
        url = str(bases[0]) if bases else ""
        nid = f"candidate:{cid}"
        add_node(
            GraphNode(
                id=nid,
                kind="candidate",
                label=str(entry.get("name") or cid),
                url=url,
                depth=1,
                score=28.0,
                metadata={"manifest_candidate": cid, "tier": entry.get("tier"), "notes": entry.get("notes")},
            )
        )
        add_edge(GraphEdge(src="registry:wikidata", dst=nid, relation="manifest_candidate"))
        breadth_count += 1

    # Depth pass: promote URL nodes discovered at depth<max_depth via BFS queue
    queue: deque[tuple[str, int]] = deque()
    for n in nodes.values():
        if n.kind in ("entity", "registry_source") and n.depth < max_depth:
            queue.append((n.id, n.depth))

    visited_depth: set[str] = set()
    while queue and len(nodes) < max_nodes:
        node_id, depth = queue.popleft()
        if node_id in visited_depth:
            continue
        visited_depth.add(node_id)
        node = nodes.get(node_id)
        if not node or depth >= max_depth:
            continue
        # URL children already attached from wikidata; link high-score URLs to registry gap
        for edge in [e for e in edges if e.src == node_id]:
            child = nodes.get(edge.dst)
            if child and child.kind == "url" and child.depth <= max_depth:
                if child.score >= 15 and child.id not in visited_depth:
                    queue.append((child.id, child.depth))

    # Build ranked candidates (URLs not already in registry)
    registered_ids = set(registry.keys())
    registered_domains = {_domain(u) for u in known_urls if u}
    candidates: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()
    for node in sorted(nodes.values(), key=lambda n: n.score, reverse=True):
        if node.kind not in ("url", "candidate"):
            continue
        if node.score < 10:
            continue
        url = node.url or ""
        if not url:
            continue
        dom = _domain(url)
        if dom in registered_domains:
            continue
        cand_id = _domain_slug(url)
        if cand_id in registered_ids or cand_id in seen_candidate_ids:
            continue
        hint = next((DOMAIN_AUTHORITY_HINTS[d] for d in DOMAIN_AUTHORITY_HINTS if dom == d or dom.endswith("." + d)), {})
        seen_candidate_ids.add(cand_id)
        candidates.append(
            {
                "id": cand_id,
                "name": node.label or cand_id,
                "base_urls": [f"https://{dom}/"],
                "tier": hint.get("tier") or node.metadata.get("tier") or "B",
                "origin_class": hint.get("origin_class") or "encyclopedia",
                "score": round(node.score, 2),
                "url": url,
                "discovery_node": node.id,
                "notes": f"REQ-009 discovery (score={node.score:.0f}); verify ToS before crawl.",
            }
        )

    graph = {
        "nodes": [asdict(n) for n in sorted(nodes.values(), key=lambda x: (-x.score, x.id))[:max_nodes]],
        "edges": [asdict(e) for e in edges[: max_nodes * 2]],
    }
    return {
        "graph": graph,
        "candidates": candidates[:max_breadth],
        "seed_hints": seed_hints,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "candidate_count": len(candidates),
            "max_depth": max_depth,
            "max_breadth": max_breadth,
        },
    }


def enqueue_seed_authority_crawl(
    db: Session,
    *,
    seed_hints: dict[str, Any] | None = None,
    composer_id: str = "",
    wikidata_qid: str = "",
    wikipedia_title: str = "",
    sync: bool | None = None,
) -> list[dict[str, Any]]:
    """Enqueue verified-source crawl jobs for the exploration seed entity."""
    from aulos_knowledge.config import get_settings

    hints = dict(seed_hints or {})
    composer_id = str(composer_id or hints.get("composer_id") or "")
    wikidata_qid = str(wikidata_qid or hints.get("wikidata_qid") or "").upper()
    wikipedia_title = str(wikipedia_title or hints.get("wikipedia_title") or "")
    musicbrainz_id = str(hints.get("musicbrainz_id") or "")
    imslp_page = str(hints.get("imslp_page") or "")

    settings = get_settings()
    run_sync = settings.sync_jobs if sync is None else sync
    jobs: list[dict[str, Any]] = []

    def _try(source_id: str, params: dict[str, Any]) -> None:
        if not _source_crawlable(db, source_id):
            jobs.append({"source_id": source_id, "status": "skipped", "reason": "not_crawl_ready"})
            return
        job = enqueue_fetch_job(db, source_id=source_id, params=params, sync=run_sync)
        jobs.append({"source_id": source_id, "job_id": job.id, "status": job.status})

    if wikidata_qid:
        _try("wikidata", {"qids": [wikidata_qid], "composer_id": composer_id})
    if wikipedia_title:
        _try(
            "wikipedia",
            {"title": wikipedia_title, "langs": ["en", "zh"], "composer_id": composer_id},
        )
    if musicbrainz_id:
        _try(
            "musicbrainz",
            {
                "mode": "artist",
                "query": f'arid:{musicbrainz_id}',
                "composer_id": composer_id,
            },
        )
    elif composer_id or wikipedia_title:
        query = wikipedia_title or composer_id.replace("-", " ")
        _try("musicbrainz", {"mode": "artist", "query": query, "composer_id": composer_id})
    if imslp_page:
        _try("imslp", {"title": imslp_page, "composer_id": composer_id})

    return jobs


def execute_discovery_run(
    db: Session,
    *,
    composer_id: str = "",
    wikidata_qid: str = "",
    max_depth: int = 2,
    max_breadth: int = 24,
    trigger: str = "ops",
    enqueue_crawl: bool = False,
    wikipedia_title: str = "",
    sync: bool | None = None,
) -> SourceDiscoveryRun:
    row = SourceDiscoveryRun(
        status="running",
        trigger=trigger,
        composer_id=composer_id,
        wikidata_qid=wikidata_qid,
        started_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        result = run_source_discovery(
            db,
            composer_id=composer_id,
            wikidata_qid=wikidata_qid,
            max_depth=max_depth,
            max_breadth=max_breadth,
        )
        hints = dict(result.get("seed_hints") or {})
        if wikipedia_title:
            hints["wikipedia_title"] = wikipedia_title
        crawl_jobs: list[dict[str, Any]] = []
        if enqueue_crawl and (hints.get("wikidata_qid") or hints.get("wikipedia_title") or composer_id):
            crawl_jobs = enqueue_seed_authority_crawl(
                db,
                seed_hints=hints,
                composer_id=composer_id,
                wikidata_qid=wikidata_qid,
                wikipedia_title=wikipedia_title,
                sync=sync,
            )
        stats = dict(result["stats"])
        stats["crawl_jobs"] = crawl_jobs
        stats["seed_hints"] = hints
        row.status = "succeeded"
        row.graph_json = json.dumps(result["graph"], ensure_ascii=False)
        row.candidates_json = json.dumps(result["candidates"], ensure_ascii=False)
        row.stats_json = json.dumps(stats, ensure_ascii=False)
        row.finished_at = utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("discovery_run_failed id=%s", row.id)
        row.status = "failed"
        row.error = str(exc)[:2000]
        row.finished_at = utcnow()
        db.commit()
        raise
    db.refresh(row)
    return row


def discovery_run_dict(row: SourceDiscoveryRun) -> dict[str, Any]:
    def _loads(raw: str, default: Any) -> Any:
        try:
            return json.loads(raw or "")
        except json.JSONDecodeError:
            return default

    stats = _loads(row.stats_json, {})
    return {
        "id": row.id,
        "status": row.status,
        "trigger": row.trigger,
        "composer_id": row.composer_id or "",
        "wikidata_qid": row.wikidata_qid or "",
        "graph": _loads(row.graph_json, {}),
        "candidates": _loads(row.candidates_json, []),
        "stats": stats,
        "seed_hints": stats.get("seed_hints") if isinstance(stats, dict) else {},
        "crawl_jobs": stats.get("crawl_jobs") if isinstance(stats, dict) else [],
        "error": row.error or "",
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
    }


def enqueue_discovery_crawl(
    db: Session,
    run_id: int,
    *,
    sync: bool | None = None,
) -> dict[str, Any]:
    """Re-enqueue authority crawl for an existing discovery run's seed."""
    row = db.get(SourceDiscoveryRun, run_id)
    if not row:
        raise ValueError(f"discovery run not found: {run_id}")
    try:
        stats = json.loads(row.stats_json or "{}")
    except json.JSONDecodeError:
        stats = {}
    hints = dict(stats.get("seed_hints") or {})
    if not hints.get("wikidata_qid"):
        hints["wikidata_qid"] = row.wikidata_qid or ""
    if not hints.get("composer_id"):
        hints["composer_id"] = row.composer_id or ""
    jobs = enqueue_seed_authority_crawl(db, seed_hints=hints, sync=sync)
    stats["crawl_jobs"] = jobs
    stats["seed_hints"] = hints
    row.stats_json = json.dumps(stats, ensure_ascii=False)
    db.commit()
    return {"run_id": run_id, "crawl_jobs": jobs, "seed_hints": hints}


def register_discovery_candidates(
    db: Session,
    run_id: int,
    *,
    candidate_ids: list[str] | None = None,
    min_score: float = 10.0,
) -> dict[str, Any]:
    row = db.get(SourceDiscoveryRun, run_id)
    if not row:
        raise ValueError(f"discovery run not found: {run_id}")
    try:
        candidates = json.loads(row.candidates_json or "[]")
    except json.JSONDecodeError:
        candidates = []
    want = set(candidate_ids) if candidate_ids else None
    created: list[str] = []
    skipped: list[str] = []
    for cand in candidates:
        cid = str(cand.get("id") or "")
        if not cid:
            continue
        if float(cand.get("score") or 0) < min_score:
            skipped.append(cid)
            continue
        if want is not None and cid not in want:
            continue
        if db.get(SourceAuthority, cid):
            skipped.append(cid)
            continue
        base_urls = list(cand.get("base_urls") or [])
        if not base_urls and cand.get("url"):
            dom = _domain(str(cand["url"]))
            base_urls = [f"https://{dom}/"]
        new_row = SourceAuthority(
            id=cid,
            name=str(cand.get("name") or cid),
            tier=str(cand.get("tier") or "B"),
            connector="",
            base_urls_json=json.dumps(base_urls, ensure_ascii=False),
            license_class="unknown",
            rate_limit_qps=1.0,
            enabled=False,
            notes=str(cand.get("notes") or "REQ-009 discovery candidate"),
            verification_status="candidate",
            origin_class=str(cand.get("origin_class") or "encyclopedia"),
        )
        db.add(new_row)
        created.append(cid)
    db.commit()
    return {"created": created, "skipped": skipped, "run_id": run_id}
