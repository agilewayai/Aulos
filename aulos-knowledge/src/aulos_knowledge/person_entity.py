"""REQ-011 / SPEC-011 — resolve person entity card: strict KB match, then Discogs → Wikidata/Wikipedia."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy.orm import Session

from aulos_knowledge.db import ComposerEntity, KnowledgeChunk, KnowledgeDocument, SourceAuthority
from aulos_knowledge.publish_policy import document_status_for_source
from aulos_knowledge.retrieve import retrieve as kb_retrieve

logger = logging.getLogger("aulos_knowledge.person_entity")

UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; person-entity-card)"
EXTRACTOR = "person-entity/0.2.0"
_TOKEN = re.compile(r"[a-z0-9\u4e00-\u9fff]+", re.I)
_CJK = re.compile(r"[\u4e00-\u9fff]")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", (name or "").strip().lower()).strip("-")
    return (s or "person")[:96]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _tokens(s: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(s or "") if t]


def _has_cjk(s: str) -> bool:
    return bool(_CJK.search(s or ""))


def _aliases(row: ComposerEntity) -> list[str]:
    try:
        raw = json.loads(row.aliases_json or "[]")
        if isinstance(raw, list):
            return [str(x) for x in raw if x]
    except json.JSONDecodeError:
        pass
    return []


def names_compatible(query: str, candidate: str) -> bool:
    """Strict identity check — never treat unrelated corpus hits as the same person."""
    q = _norm(query)
    c = _norm(candidate)
    if not q or not c:
        return False
    if q == c:
        return True
    # CJK: exact only (no substring / soft match — 朱莉亚尼 must not hit 巴赫)
    if _has_cjk(q) or _has_cjk(c):
        return False
    qt, ct = _tokens(q), _tokens(c)
    if not qt or not ct:
        return False
    # Full query equals any contiguous candidate token sequence
    if " ".join(qt) == " ".join(ct):
        return True
    # Single Latin token may match unique surname (last token) — caller may further uniquify
    if len(qt) == 1 and len(qt[0]) >= 4 and qt[0] == ct[-1]:
        return True
    # Multi-token query: every query token must appear in candidate (order-free),
    # and at least half of candidate tokens covered — blocks Bach⊂Giuliani nonsense
    if len(qt) >= 2 and set(qt) <= set(ct) and len(set(qt) & set(ct)) >= max(2, (len(ct) + 1) // 2):
        return True
    return False


def find_local_person(db: Session, name: str) -> ComposerEntity | None:
    needle = _norm(name)
    if not needle:
        return None

    rows = db.query(ComposerEntity).all()
    exact: list[ComposerEntity] = []
    surname: list[ComposerEntity] = []

    for row in rows:
        candidates = [row.name_en, row.name_zh, row.id, *_aliases(row)]
        for c in candidates:
            cn = _norm(c)
            if not cn:
                continue
            if cn == needle or _norm(c.replace("-", " ")) == needle.replace("-", " "):
                exact.append(row)
                break
            if names_compatible(needle, c) and not _has_cjk(needle):
                # surname-style soft match collected separately
                qt = _tokens(needle)
                ct = _tokens(c)
                if len(qt) == 1 and ct and qt[0] == ct[-1]:
                    surname.append(row)
                    break
                if len(qt) >= 2 and names_compatible(needle, c):
                    exact.append(row)
                    break

    if exact:
        # Prefer exact name_en/zh over id-only
        return exact[0]
    # Surname match only when unique in corpus
    uniq = {r.id: r for r in surname}
    if len(uniq) == 1:
        return next(iter(uniq.values()))
    return None


def _source_ok(db: Session, source_id: str) -> SourceAuthority | None:
    src = db.get(SourceAuthority, source_id)
    if src is None:
        return None
    if not src.enabled or src.verification_status != "verified":
        return None
    return src


def _filter_hits_for_person(
    hits: list[dict[str, Any]],
    *,
    name: str,
    person_id: str,
) -> list[dict[str, Any]]:
    """Only keep snippets that clearly belong to this person — never borrow Bach for Giuliani."""
    out: list[dict[str, Any]] = []
    for h in hits:
        eid = str(h.get("entity_id") or "")
        if person_id and eid and eid == person_id:
            out.append(h)
            continue
        blob = f"{h.get('title') or ''} {h.get('text') or ''}"
        if names_compatible(name, str(h.get("title") or "")):
            out.append(h)
            continue
        # require query name tokens to appear in snippet with strong overlap
        if _has_cjk(name):
            if _norm(name) in _norm(blob):
                out.append(h)
            continue
        qt = set(_tokens(name))
        bt = set(_tokens(blob))
        if qt and qt <= bt:
            out.append(h)
    return out


def _card_from_local(
    db: Session,
    *,
    name: str,
    kind: str,
    row: ComposerEntity | None,
    hits: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = ""
    lifespan = ""
    era = ""
    display = name
    person_id = _slug(name)
    ext: dict[str, Any] = {}
    if row is not None:
        summary = (row.summary_zh or row.summary_en or "").strip()
        lifespan = row.lifespan or ""
        era = row.era or ""
        display = row.name_zh or row.name_en or name
        person_id = row.id
        try:
            parsed = json.loads(row.external_ids_json or "{}")
            if isinstance(parsed, dict):
                ext = parsed
        except json.JSONDecodeError:
            ext = {}
    safe_hits = _filter_hits_for_person(hits, name=name, person_id=person_id if row else "")
    # Without a matched composer row, RAG hits alone must NOT invent identity
    if row is None:
        safe_hits = []
    if not summary and safe_hits:
        summary = str(safe_hits[0].get("text") or "")[:800]
    rich = row is not None and (bool(summary) or bool(safe_hits))
    return {
        "name": name,
        "kind": kind,
        "person_id": person_id if row is not None else "",
        "display_name": display,
        "lifespan": lifespan,
        "era": era,
        "summary": summary if row is not None else "",
        "portrait_url": "",
        "external_ids": ext,
        "snippets": [
            {
                "title": h.get("title") or "",
                "text": (h.get("text") or "")[:500],
                "source_id": h.get("source_id") or "",
                "score": h.get("score"),
            }
            for h in safe_hits[:5]
        ],
        "source": "knowledge" if rich else "unresolved",
        "provenance": [],
        "matched": row is not None,
    }


def _wikidata_hit_matches(name: str, hit: dict[str, Any]) -> bool:
    if names_compatible(name, str(hit.get("label") or "")):
        return True
    match_text = str((hit.get("match") or {}).get("text") or "")
    if match_text and _norm(match_text) == _norm(name):
        return True
    for al in hit.get("aliases") or []:
        if _norm(str(al)) == _norm(name) or names_compatible(name, str(al)):
            return True
    return False


def _wikidata_search(client: httpx.Client, name: str) -> dict[str, Any] | None:
    url = "https://www.wikidata.org/w/api.php"
    resp = client.get(
        url,
        params={
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "uselang": "zh" if _has_cjk(name) else "en",
            "type": "item",
            "limit": "8",
            "format": "json",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("search") or []
    if not hits:
        return None
    music_re = re.compile(
        r"(?i)\b(composer|pianist|violinist|conductor|orchestra|musician|singer|cellist|guitarist)\b"
    )
    pool = [h for h in hits if _wikidata_hit_matches(name, h)]
    if not pool:
        return None
    ranked = sorted(
        pool,
        key=lambda h: (0 if music_re.search(str(h.get("description") or "")) else 1, str(h.get("label") or "")),
    )
    return ranked[0]


def _wikidata_entity(client: httpx.Client, qid: str) -> dict[str, Any]:
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    resp = client.get(url)
    resp.raise_for_status()
    return (resp.json().get("entities") or {}).get(qid) or {}


def _wikipedia_summary(client: httpx.Client, title: str, *, lang: str = "en") -> dict[str, Any] | None:
    if not title:
        return None
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
    resp = client.get(url)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else None


def _lifespan_from_entity(entity: dict[str, Any]) -> str:
    claims = entity.get("claims") or {}

    def year(prop: str) -> str:
        vals = claims.get(prop) or []
        if not vals:
            return ""
        t = (((vals[0] or {}).get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
        raw = str(t.get("time") or "")
        if len(raw) >= 5 and raw[0] in "+-":
            return raw[1:5]
        return ""

    b, d = year("P569"), year("P570")
    if b and d:
        return f"{b}–{d}"
    return b or d or ""


def persist_person_card(
    db: Session,
    *,
    name: str,
    kind: str,
    display_name: str,
    summary: str,
    lifespan: str = "",
    era: str = "",
    portrait_url: str = "",
    external_ids: dict[str, Any] | None = None,
    provenance: list[dict[str, str]] | None = None,
    source_id: str = "discogs",
    body_title: str = "",
) -> dict[str, Any]:
    """Upsert composer + knowledge doc from an external authority card (Discogs-first path)."""
    label = (display_name or name).strip() or name.strip()
    person_id = _slug(label)
    ext = dict(external_ids or {})
    ext.setdefault("person_kind", kind)

    # Famous identity lock when slug matches allowlist
    try:
        from aulos_knowledge.famous_composers import famous_by_id

        famous = famous_by_id().get(person_id)
    except Exception:  # noqa: BLE001
        famous = None
    if famous and famous.get("wikidata_qid"):
        ext["wikidata"] = str(famous["wikidata_qid"]).upper()
        label = str(famous.get("name_en") or label)
        if famous.get("era") and not era:
            era = str(famous["era"])

    existing = db.get(ComposerEntity, person_id)
    summary_en = summary if not _has_cjk(summary) else ""
    summary_zh = summary if _has_cjk(summary) else ""
    # Prefer writing into both fields lightly when Latin profile
    if summary and not summary_zh and not summary_en:
        summary_en = summary
    if existing is None:
        row = ComposerEntity(
            id=person_id,
            name_en=label if not _has_cjk(label) else "",
            name_zh=label if _has_cjk(label) else "",
            aliases_json=json.dumps(list({name, label}), ensure_ascii=False),
            external_ids_json=json.dumps(ext, ensure_ascii=False),
            lifespan=lifespan or "",
            era=era or "",
            summary_en=summary_en or (summary if not _has_cjk(summary) else ""),
            summary_zh=summary_zh,
        )
        if not row.name_en and not row.name_zh:
            row.name_en = label
        if summary and not row.summary_en and not row.summary_zh:
            row.summary_en = summary
        db.add(row)
    else:
        row = existing
        aliases = set(_aliases(row))
        aliases.update({name, label})
        row.aliases_json = json.dumps(sorted(aliases), ensure_ascii=False)
        if summary:
            if _has_cjk(summary) and not row.summary_zh:
                row.summary_zh = summary
            elif not row.summary_en:
                row.summary_en = summary
        if lifespan and not row.lifespan:
            row.lifespan = lifespan
        try:
            cur = json.loads(row.external_ids_json or "{}")
            if not isinstance(cur, dict):
                cur = {}
        except json.JSONDecodeError:
            cur = {}
        cur.update({k: v for k, v in ext.items() if v})
        if famous and famous.get("wikidata_qid"):
            cur["wikidata"] = str(famous["wikidata_qid"]).upper()
        row.external_ids_json = json.dumps(cur, ensure_ascii=False)

    prov = list(provenance or [])
    src = _source_ok(db, source_id) or db.get(SourceAuthority, source_id)
    if src is not None and summary:
        status = document_status_for_source(src) if _source_ok(db, source_id) else "quarantine"
        title = body_title or f"{label} — {source_id} profile"
        doc = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.entity_id == person_id,
                KnowledgeDocument.source_id == src.id,
                KnowledgeDocument.entity_type == "person",
            )
            .one_or_none()
        )
        if doc is None:
            doc = KnowledgeDocument(
                source_id=src.id,
                entity_type="person",
                entity_id=person_id,
                title=title,
                body=summary,
                status=status,
                license_class=src.license_class or "",
                extractor_version=EXTRACTOR,
            )
            db.add(doc)
            db.flush()
            db.add(
                KnowledgeChunk(
                    document_id=doc.id,
                    section="summary",
                    text=summary[:4000],
                    aulos_work_id="",
                )
            )
        else:
            doc.body = summary
            doc.title = title
            doc.status = status
            chunk = (
                db.query(KnowledgeChunk)
                .filter(KnowledgeChunk.document_id == doc.id, KnowledgeChunk.section == "summary")
                .one_or_none()
            )
            if chunk is None:
                db.add(
                    KnowledgeChunk(
                        document_id=doc.id,
                        section="summary",
                        text=summary[:4000],
                        aulos_work_id="",
                    )
                )
            else:
                chunk.text = summary[:4000]

    db.commit()
    return {
        "name": name,
        "kind": kind,
        "person_id": person_id,
        "display_name": label,
        "lifespan": lifespan or (existing.lifespan if existing else "") or "",
        "era": era or "",
        "summary": summary,
        "portrait_url": portrait_url,
        "external_ids": ext,
        "snippets": [],
        "source": "enriched",
        "provenance": prov,
        "matched": True,
    }


def enrich_from_authorities(
    db: Session,
    *,
    name: str,
    kind: str,
    client: httpx.Client | None = None,
) -> dict[str, Any] | None:
    wiki_src = _source_ok(db, "wikipedia")
    wd_src = _source_ok(db, "wikidata")
    if wiki_src is None and wd_src is None:
        return None

    own = client is None
    http = client or httpx.Client(timeout=25.0, headers={"User-Agent": UA}, follow_redirects=True)
    try:
        hit = _wikidata_search(http, name) if wd_src is not None else None
        if hit is None:
            return None
        qid = str((hit or {}).get("id") or "")
        label = str((hit or {}).get("label") or name)
        description = str((hit or {}).get("description") or "")
        entity: dict[str, Any] = {}
        enwiki = ""
        zhwiki = ""
        if qid and wd_src is not None:
            entity = _wikidata_entity(http, qid)
            sitelinks = entity.get("sitelinks") or {}
            enwiki = str((sitelinks.get("enwiki") or {}).get("title") or "")
            zhwiki = str((sitelinks.get("zhwiki") or {}).get("title") or "")
            labels = entity.get("labels") or {}
            if (labels.get("en") or {}).get("value"):
                label = str(labels["en"]["value"])
            zh_label = (labels.get("zh") or labels.get("zh-hans") or {}).get("value")
            if _has_cjk(name) and zh_label:
                label = str(zh_label)

        # Must still be the searched person (search already filtered; re-check Latin)
        if not _has_cjk(name) and not (
            names_compatible(name, label) or names_compatible(name, enwiki or "") or _wikidata_hit_matches(name, hit)
        ):
            return None

        summary_payload = None
        used_lang = "en"
        used_title = enwiki or label
        if wiki_src is not None:
            if _has_cjk(name) and zhwiki:
                summary_payload = _wikipedia_summary(http, zhwiki, lang="zh")
                if summary_payload:
                    used_lang = "zh"
                    used_title = zhwiki
            if summary_payload is None:
                summary_payload = _wikipedia_summary(http, enwiki or label, lang="en")
            if summary_payload is None and zhwiki and used_lang != "zh":
                summary_payload = _wikipedia_summary(http, zhwiki, lang="zh")
                used_lang = "zh"
                used_title = zhwiki
        extract = ""
        portrait = ""
        page_url = ""
        if summary_payload:
            extract = str(summary_payload.get("extract") or "").strip()
            portrait = str(((summary_payload.get("thumbnail") or {}).get("source")) or "")
            page_url = str(((summary_payload.get("content_urls") or {}).get("desktop") or {}).get("page") or "")
            if summary_payload.get("title"):
                used_title = str(summary_payload["title"])

        if not extract and description:
            extract = description

        if not extract and not qid:
            return None

        card = persist_person_card(
            db,
            name=name,
            kind=kind,
            display_name=label,
            summary=extract,
            lifespan=_lifespan_from_entity(entity) if entity else "",
            portrait_url=portrait,
            external_ids={
                "wikidata": qid,
                "enwiki": enwiki,
                "zhwiki": zhwiki,
                "person_kind": kind,
            },
            provenance=(
                ([{"source_id": "wikipedia", "url": page_url}] if page_url else [])
                + ([{"source_id": "wikidata", "url": f"https://www.wikidata.org/wiki/{qid}"}] if qid else [])
            ),
            source_id="wikidata" if wd_src is not None else "wikipedia",
            body_title=f"{label} — encyclopedia card",
        )
        card["wikipedia_title"] = used_title
        return card
    except Exception as exc:  # noqa: BLE001
        logger.warning("person_enrich_failed name=%s err=%s", name, exc)
        db.rollback()
        return None
    finally:
        if own:
            http.close()


def resolve_person_card(
    db: Session,
    *,
    name: str,
    kind: str = "person",
    enrich: bool = True,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    clean = (name or "").strip()
    if not clean:
        raise ValueError("name required")
    kind_norm = (kind or "person").strip().lower() or "person"
    if kind_norm not in {"composer", "performer", "ensemble", "person"}:
        kind_norm = "person"

    from aulos_knowledge.person_aggregate import (
        aggregate_person_card,
        bilingual_complete,
        card_from_composer_row,
    )

    row = find_local_person(db, clean)
    if row is not None:
        local_card = card_from_composer_row(db, name=clean, kind=kind_norm, row=row)
        if bilingual_complete(local_card) or not enrich:
            # enrich=false: return whatever we have locally (may be monolingual)
            if not enrich:
                return local_card
            return local_card
        # monolingual or thin — fall through to aggregate to fill gaps
    elif not enrich:
        return _card_from_local(db, name=clean, kind=kind_norm, row=None, hits=[])

    return aggregate_person_card(
        db,
        name=clean,
        kind=kind_norm,
        fragments=None,
        fetch_remote=True,
        persist=True,
        client=client,
    )
