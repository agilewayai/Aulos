"""REQ-012 / SPEC-012 — multi-source field merge + bilingual person cards."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from aulos_knowledge.db import ComposerEntity, KnowledgeChunk, KnowledgeDocument, SourceAuthority
from aulos_knowledge.person_entity import (
    EXTRACTOR,
    UA,
    _aliases,
    _card_from_local,
    _has_cjk,
    _lifespan_from_entity,
    _norm,
    _slug,
    _source_ok,
    _wikidata_entity,
    _wikidata_search,
    _wikipedia_summary,
    find_local_person,
    names_compatible,
)
from aulos_knowledge.publish_policy import document_status_for_source
from aulos_knowledge.retrieve import retrieve as kb_retrieve

logger = logging.getLogger("aulos_knowledge.person_aggregate")

AGG_VERSION = "person-agg/0.1.0"


def _pick(*vals: str) -> str:
    for v in vals:
        s = (v or "").strip()
        if s:
            return s
    return ""


def _merge_aliases(*groups: list[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for raw in group or []:
            s = str(raw).strip()
            if not s:
                continue
            key = _norm(s)
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
    return out


def fragment_from_local(row: ComposerEntity | None, *, name: str, kind: str) -> dict[str, Any] | None:
    if row is None:
        return None
    try:
        ext = json.loads(row.external_ids_json or "{}")
        if not isinstance(ext, dict):
            ext = {}
    except json.JSONDecodeError:
        ext = {}
    return {
        "source_id": "local",
        "role": "cache",
        "display_name_en": row.name_en or "",
        "display_name_zh": row.name_zh or "",
        "summary_en": row.summary_en or "",
        "summary_zh": row.summary_zh or "",
        "summary_en_origin": "local" if row.summary_en else "",
        "summary_zh_origin": "local" if row.summary_zh else "",
        "lifespan": row.lifespan or "",
        "era": row.era or "",
        "portrait_url": "",
        "external_ids": ext,
        "aliases": _aliases(row) + [name, row.name_en, row.name_zh, row.id],
        "provenance": [],
        "person_id_hint": row.id,
        "kind": kind,
    }


def fragment_from_discogs_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize API Discogs artist card into an aggregate fragment."""
    summary = str(payload.get("summary") or "").strip()
    display = str(payload.get("display_name") or payload.get("name") or "").strip()
    ext = dict(payload.get("external_ids") or {})
    aliases = [display, str(payload.get("name") or "")]
    aliases.extend(str(x) for x in (ext.get("namevariations") or []) if x)
    if ext.get("realname"):
        aliases.append(str(ext["realname"]))
    return {
        "source_id": "discogs",
        "role": "catalog_profile",
        "display_name_en": display if not _has_cjk(display) else "",
        "display_name_zh": display if _has_cjk(display) else "",
        "summary_en": summary if summary and not _has_cjk(summary) else "",
        "summary_zh": summary if summary and _has_cjk(summary) else "",
        "summary_en_origin": "discogs" if summary and not _has_cjk(summary) else "",
        "summary_zh_origin": "discogs" if summary and _has_cjk(summary) else "",
        "lifespan": str(payload.get("lifespan") or ""),
        "era": str(payload.get("era") or ""),
        "portrait_url": str(payload.get("portrait_url") or ""),
        "external_ids": {k: v for k, v in ext.items() if k != "namevariations"},
        "aliases": aliases,
        "provenance": list(payload.get("provenance") or []),
        "fields": ["summary_en", "portrait_url", "aliases"],
    }


def fetch_wikidata_wikipedia_fragments(
    client: httpx.Client,
    *,
    name: str,
    db: Session,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    wd_src = _source_ok(db, "wikidata")
    wiki_src = _source_ok(db, "wikipedia")
    if wd_src is None and wiki_src is None:
        return out

    hit = _wikidata_search(client, name) if wd_src is not None else None
    if hit is None:
        return out

    qid = str(hit.get("id") or "")
    label = str(hit.get("label") or name)
    description = str(hit.get("description") or "")
    entity: dict[str, Any] = {}
    enwiki = ""
    zhwiki = ""
    name_en = label
    name_zh = ""
    desc_en = description
    desc_zh = ""

    if qid and wd_src is not None:
        entity = _wikidata_entity(client, qid)
        sitelinks = entity.get("sitelinks") or {}
        enwiki = str((sitelinks.get("enwiki") or {}).get("title") or "")
        zhwiki = str((sitelinks.get("zhwiki") or {}).get("title") or "")
        labels = entity.get("labels") or {}
        if (labels.get("en") or {}).get("value"):
            name_en = str(labels["en"]["value"])
        zh_lab = (labels.get("zh") or labels.get("zh-hans") or {}).get("value")
        if zh_lab:
            name_zh = str(zh_lab)
        descriptions = entity.get("descriptions") or {}
        if (descriptions.get("en") or {}).get("value"):
            desc_en = str(descriptions["en"]["value"])
        zh_desc = (descriptions.get("zh") or descriptions.get("zh-hans") or {}).get("value")
        if zh_desc:
            desc_zh = str(zh_desc)

    out.append(
        {
            "source_id": "wikidata",
            "role": "identity",
            "display_name_en": name_en,
            "display_name_zh": name_zh,
            "summary_en": desc_en,
            "summary_zh": desc_zh,
            "summary_en_origin": "wikidata" if desc_en else "",
            "summary_zh_origin": "wikidata" if desc_zh else "",
            "lifespan": _lifespan_from_entity(entity) if entity else "",
            "era": "",
            "portrait_url": "",
            "external_ids": {
                "wikidata": qid,
                "enwiki": enwiki,
                "zhwiki": zhwiki,
            },
            "aliases": [name, name_en, name_zh, enwiki, zhwiki],
            "provenance": (
                [{"source_id": "wikidata", "url": f"https://www.wikidata.org/wiki/{qid}"}] if qid else []
            ),
            "fields": ["lifespan", "names", "external_ids"],
        }
    )

    if wiki_src is not None:
        en_sum = _wikipedia_summary(client, enwiki or name_en, lang="en") if (enwiki or name_en) else None
        zh_title = zhwiki or name_zh
        zh_sum = _wikipedia_summary(client, zh_title, lang="zh") if zh_title else None
        if en_sum:
            extract = str(en_sum.get("extract") or "").strip()
            thumb = str(((en_sum.get("thumbnail") or {}).get("source")) or "")
            page = str(((en_sum.get("content_urls") or {}).get("desktop") or {}).get("page") or "")
            out.append(
                {
                    "source_id": "wikipedia",
                    "role": "encyclopedia",
                    "lang": "en",
                    "display_name_en": str(en_sum.get("title") or name_en),
                    "display_name_zh": "",
                    "summary_en": extract,
                    "summary_zh": "",
                    "summary_en_origin": "wikipedia" if extract else "",
                    "summary_zh_origin": "",
                    "lifespan": "",
                    "era": "",
                    "portrait_url": thumb,
                    "external_ids": {"enwiki": str(en_sum.get("title") or enwiki)},
                    "aliases": [str(en_sum.get("title") or "")],
                    "provenance": [{"source_id": "wikipedia", "url": page}] if page else [],
                    "fields": ["summary_en", "portrait_url"],
                }
            )
        if zh_sum:
            extract = str(zh_sum.get("extract") or "").strip()
            thumb = str(((zh_sum.get("thumbnail") or {}).get("source")) or "")
            page = str(((zh_sum.get("content_urls") or {}).get("desktop") or {}).get("page") or "")
            out.append(
                {
                    "source_id": "wikipedia",
                    "role": "encyclopedia",
                    "lang": "zh",
                    "display_name_en": "",
                    "display_name_zh": str(zh_sum.get("title") or name_zh),
                    "summary_en": "",
                    "summary_zh": extract,
                    "summary_en_origin": "",
                    "summary_zh_origin": "wikipedia" if extract else "",
                    "lifespan": "",
                    "era": "",
                    "portrait_url": thumb,
                    "external_ids": {"zhwiki": str(zh_sum.get("title") or zhwiki)},
                    "aliases": [str(zh_sum.get("title") or "")],
                    "provenance": [{"source_id": "wikipedia", "url": page}] if page else [],
                    "fields": ["summary_zh"],
                }
            )
    return out


def _usable_summary(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 12:
        return False
    low = t.lower()
    if low.startswith("please note") or t.startswith("请注意"):
        return False
    if t.rstrip().endswith("是。") and len(t) < 48:
        return False
    if t.rstrip().endswith(" is .") or t.rstrip().endswith(" is."):
        return False
    return True


def merge_fragments(
    *,
    name: str,
    kind: str,
    fragments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Field-level merge per SPEC-012 precedence."""
    if not fragments:
        return {
            "name": name,
            "kind": kind,
            "person_id": "",
            "display_name": name,
            "display_name_en": "",
            "display_name_zh": "",
            "lifespan": "",
            "era": "",
            "summary": "",
            "summary_en": "",
            "summary_zh": "",
            "summary_en_origin": "",
            "summary_zh_origin": "",
            "portrait_url": "",
            "external_ids": {"person_kind": kind},
            "sources": [],
            "snippets": [],
            "provenance": [],
            "aliases": [],
            "source": "unresolved",
            "matched": False,
            "locale_default": "zh",
            "aggregation": {"strategy": "field-merge", "revision": AGG_VERSION},
        }

    by_src = {str(f.get("source_id") or ""): f for f in fragments}
    local = by_src.get("local") or {}
    discogs = by_src.get("discogs") or {}
    wikidata = by_src.get("wikidata") or {}
    wiki_en = next((f for f in fragments if f.get("source_id") == "wikipedia" and f.get("lang") == "en"), {})
    wiki_zh = next((f for f in fragments if f.get("source_id") == "wikipedia" and f.get("lang") == "zh"), {})
    wiki_any = next((f for f in fragments if f.get("source_id") == "wikipedia" and not f.get("lang")), {})

    def from_srcs(key: str, *srcs: dict[str, Any]) -> tuple[str, str]:
        for src in srcs:
            val = str(src.get(key) or "").strip()
            if val and _usable_summary(val):
                origin = str(src.get(f"{key}_origin") or src.get("source_id") or "")
                return val, origin
        # fallback: allow short wikidata descriptions
        for src in srcs:
            val = str(src.get(key) or "").strip()
            if val and len(val) >= 8 and not val.startswith("请注意") and not val.lower().startswith("please note"):
                origin = str(src.get(f"{key}_origin") or src.get("source_id") or "")
                return val, origin
        return "", ""

    summary_en, summary_en_origin = from_srcs(
        "summary_en",
        wiki_en or wiki_any,
        discogs,
        wikidata,
        local,
    )
    if wiki_en.get("summary_en") and _usable_summary(str(wiki_en.get("summary_en") or "")):
        summary_en = str(wiki_en["summary_en"]).strip()
        summary_en_origin = "wikipedia"
    elif discogs.get("summary_en") and _usable_summary(str(discogs.get("summary_en") or "")):
        if summary_en_origin == "wikidata" or not _usable_summary(summary_en):
            summary_en = str(discogs["summary_en"]).strip()
            summary_en_origin = "discogs"

    summary_zh, summary_zh_origin = from_srcs("summary_zh", wiki_zh, wikidata, local)
    if wiki_zh.get("summary_zh") and _usable_summary(str(wiki_zh.get("summary_zh") or "")):
        summary_zh = str(wiki_zh["summary_zh"]).strip()
        summary_zh_origin = "wikipedia"

    display_name_en = _pick(
        str(wikidata.get("display_name_en") or ""),
        str(discogs.get("display_name_en") or ""),
        str(local.get("display_name_en") or ""),
        str(wiki_en.get("display_name_en") or ""),
        name if not _has_cjk(name) else "",
    )
    display_name_zh = _pick(
        str(wikidata.get("display_name_zh") or ""),
        str(wiki_zh.get("display_name_zh") or ""),
        str(local.get("display_name_zh") or ""),
        str(discogs.get("display_name_zh") or ""),
        name if _has_cjk(name) else "",
    )

    lifespan = _pick(
        str(wikidata.get("lifespan") or ""),
        str(local.get("lifespan") or ""),
        str(discogs.get("lifespan") or ""),
    )
    era = _pick(str(local.get("era") or ""), str(wikidata.get("era") or ""))
    portrait = _pick(
        str(discogs.get("portrait_url") or ""),
        str(wiki_en.get("portrait_url") or ""),
        str(wiki_zh.get("portrait_url") or ""),
        str(local.get("portrait_url") or ""),
    )

    ext: dict[str, Any] = {"person_kind": kind}
    for f in fragments:
        for k, v in (f.get("external_ids") or {}).items():
            if v and k not in ext:
                ext[k] = v
            elif v and k in ("wikidata", "discogs", "enwiki", "zhwiki", "musicbrainz"):
                ext[k] = v  # prefer later authoritative overwrite for ids

    # Prefer wikidata/discogs ids explicitly
    if wikidata.get("external_ids"):
        ext.update({k: v for k, v in wikidata["external_ids"].items() if v})
    if discogs.get("external_ids"):
        for k, v in discogs["external_ids"].items():
            if v:
                ext[k] = v

    aliases = _merge_aliases(*[list(f.get("aliases") or []) for f in fragments], [name, display_name_en, display_name_zh])

    person_id = str(local.get("person_id_hint") or "")
    if not person_id:
        person_id = _slug(display_name_en or display_name_zh or name)

    locale_default = "zh" if display_name_zh or summary_zh or _has_cjk(name) else "en"
    display_name = display_name_zh if locale_default == "zh" and display_name_zh else (
        display_name_en or display_name_zh or name
    )
    summary = summary_zh if locale_default == "zh" and summary_zh else (summary_en or summary_zh)

    sources: list[dict[str, Any]] = []
    provenance: list[dict[str, str]] = []
    seen_prov: set[str] = set()
    for f in fragments:
        sid = str(f.get("source_id") or "")
        if not sid or sid == "local":
            continue
        url = ""
        for p in f.get("provenance") or []:
            if p.get("url"):
                url = str(p["url"])
                key = f"{p.get('source_id')}:{url}"
                if key not in seen_prov:
                    seen_prov.add(key)
                    provenance.append({"source_id": str(p.get("source_id") or sid), "url": url})
        sources.append(
            {
                "source_id": sid,
                "role": f.get("role") or "",
                "url": url,
                "fields": f.get("fields") or [],
                "lang": f.get("lang") or "",
            }
        )

    rich = bool(summary_en or summary_zh or lifespan or ext.get("wikidata") or ext.get("discogs"))
    return {
        "name": name,
        "kind": kind,
        "person_id": person_id if rich else "",
        "display_name": display_name,
        "display_name_en": display_name_en,
        "display_name_zh": display_name_zh,
        "lifespan": lifespan,
        "era": era,
        "summary": summary,
        "summary_en": summary_en,
        "summary_zh": summary_zh,
        "summary_en_origin": summary_en_origin,
        "summary_zh_origin": summary_zh_origin,
        "portrait_url": portrait,
        "external_ids": ext,
        "sources": sources,
        "snippets": [],
        "provenance": provenance,
        "aliases": aliases,
        "source": "aggregated" if rich else "unresolved",
        "matched": rich,
        "locale_default": locale_default,
        "aggregation": {"strategy": "field-merge", "revision": AGG_VERSION, "fragment_count": len(fragments)},
    }


def persist_bilingual_card(db: Session, card: dict[str, Any]) -> dict[str, Any]:
    """Persist merged bilingual card onto composers + per-source docs."""
    if card.get("source") == "unresolved" or not card.get("person_id"):
        return card

    person_id = str(card["person_id"])
    name = str(card.get("name") or "")
    kind = str(card.get("kind") or "person")
    name_en = str(card.get("display_name_en") or "")
    name_zh = str(card.get("display_name_zh") or "")
    summary_en = str(card.get("summary_en") or "")
    summary_zh = str(card.get("summary_zh") or "")
    lifespan = str(card.get("lifespan") or "")
    era = str(card.get("era") or "")
    ext = dict(card.get("external_ids") or {})
    aliases = list(card.get("aliases") or [])

    # Famous identity lock — seed QID + canonical name win over search/homonym merges
    try:
        from aulos_knowledge.famous_composers import famous_by_id

        famous = famous_by_id().get(person_id)
    except Exception:  # noqa: BLE001
        famous = None
    if famous:
        seed_qid = str(famous.get("wikidata_qid") or "").upper()
        if seed_qid:
            ext["wikidata"] = seed_qid
        name_en = str(famous.get("name_en") or name_en)
        if famous.get("name_zh"):
            name_zh = name_zh or str(famous["name_zh"])
        if famous.get("era") and not era:
            era = str(famous["era"])

    row = db.get(ComposerEntity, person_id)
    if row is None:
        row = ComposerEntity(
            id=person_id,
            name_en=name_en or (name if not _has_cjk(name) else ""),
            name_zh=name_zh or (name if _has_cjk(name) else ""),
            aliases_json=json.dumps(aliases, ensure_ascii=False),
            external_ids_json=json.dumps(ext, ensure_ascii=False),
            lifespan=lifespan,
            era=era,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
        db.add(row)
    else:
        if name_en and not row.name_en:
            row.name_en = name_en
        if name_zh and not row.name_zh:
            row.name_zh = name_zh
        if name_en:
            row.name_en = name_en
        if name_zh:
            row.name_zh = name_zh
        if summary_en:
            row.summary_en = summary_en
        if summary_zh:
            row.summary_zh = summary_zh
        if lifespan:
            row.lifespan = lifespan
        if era and not row.era:
            row.era = era
        merged_aliases = _merge_aliases(_aliases(row), aliases)
        row.aliases_json = json.dumps(merged_aliases, ensure_ascii=False)
        try:
            cur = json.loads(row.external_ids_json or "{}")
            if not isinstance(cur, dict):
                cur = {}
        except json.JSONDecodeError:
            cur = {}
        cur.update({k: v for k, v in ext.items() if v})
        # store origin markers for UI
        if card.get("summary_en_origin"):
            cur["summary_en_origin"] = card["summary_en_origin"]
        if card.get("summary_zh_origin"):
            cur["summary_zh_origin"] = card["summary_zh_origin"]
        if famous and famous.get("wikidata_qid"):
            cur["wikidata"] = str(famous["wikidata_qid"]).upper()
        row.external_ids_json = json.dumps(cur, ensure_ascii=False)

    # Persist one doc per contributing source with text
    for src_entry in card.get("sources") or []:
        sid = str(src_entry.get("source_id") or "")
        if not sid:
            continue
        src = _source_ok(db, sid) or db.get(SourceAuthority, sid)
        if src is None:
            continue
        lang = str(src_entry.get("lang") or "")
        body = ""
        title = f"{name_en or name_zh or name} — {sid}"
        if sid == "discogs":
            body = summary_en if card.get("summary_en_origin") == "discogs" else summary_en
            title = f"{name_en or name} — Discogs profile"
        elif sid == "wikipedia" and lang == "zh":
            body = summary_zh if card.get("summary_zh_origin") == "wikipedia" else ""
            title = f"{name_zh or name} — Wikipedia ZH"
        elif sid == "wikipedia":
            body = summary_en if card.get("summary_en_origin") == "wikipedia" else summary_en
            title = f"{name_en or name} — Wikipedia EN"
        elif sid == "wikidata":
            body = _pick(summary_en if card.get("summary_en_origin") == "wikidata" else "", summary_zh)
            title = f"{name_en or name_zh or name} — Wikidata"
        if not body:
            continue
        status = document_status_for_source(src) if _source_ok(db, sid) else "quarantine"
        entity_key = f"{sid}:{lang}" if lang else sid
        doc = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.entity_id == person_id,
                KnowledgeDocument.source_id == sid,
                KnowledgeDocument.entity_type == "person",
                KnowledgeDocument.title == title,
            )
            .one_or_none()
        )
        if doc is None:
            # fallback match by source only
            doc = (
                db.query(KnowledgeDocument)
                .filter(
                    KnowledgeDocument.entity_id == person_id,
                    KnowledgeDocument.source_id == sid,
                    KnowledgeDocument.entity_type == "person",
                )
                .first()
            )
        if doc is None:
            doc = KnowledgeDocument(
                source_id=sid,
                entity_type="person",
                entity_id=person_id,
                title=title,
                body=body,
                status=status,
                license_class=src.license_class or "",
                extractor_version=EXTRACTOR,
            )
            db.add(doc)
            db.flush()
            db.add(
                KnowledgeChunk(
                    document_id=doc.id,
                    section=f"summary:{lang or 'default'}",
                    text=body[:4000],
                    aulos_work_id="",
                )
            )
        else:
            doc.body = body
            doc.title = title
            doc.status = status
            chunk = (
                db.query(KnowledgeChunk)
                .filter(KnowledgeChunk.document_id == doc.id)
                .first()
            )
            if chunk is None:
                db.add(
                    KnowledgeChunk(
                        document_id=doc.id,
                        section=f"summary:{lang or 'default'}",
                        text=body[:4000],
                        aulos_work_id="",
                    )
                )
            else:
                chunk.text = body[:4000]
        _ = entity_key

    db.commit()
    card["source"] = "aggregated"
    card["matched"] = True
    return card


def bilingual_complete(card: dict[str, Any] | None) -> bool:
    if not isinstance(card, dict):
        return False
    if card.get("source") == "unresolved":
        return False
    en = (card.get("summary_en") or card.get("summary") or "").strip()
    zh = (card.get("summary_zh") or "").strip()
    if not _usable_summary(en) or len(zh) < 12:
        return False
    if zh.startswith("请注意") or not _usable_summary(zh) and len(zh) < 40:
        # allow short native wikidata zh if paired with solid en + identity
        if len(zh) < 8 or zh.startswith("请注意"):
            return False
    ext = card.get("external_ids") or {}
    if ext.get("wikidata") or ext.get("enwiki") or ext.get("zhwiki"):
        return _usable_summary(en) and len(zh) >= 8 and not zh.startswith("请注意")
    origins = {str(card.get("summary_en_origin") or ""), str(card.get("summary_zh_origin") or "")}
    if "wikipedia" in origins:
        return True
    return False


def card_from_composer_row(
    db: Session,
    *,
    name: str,
    kind: str,
    row: ComposerEntity,
) -> dict[str, Any]:
    retrieved = kb_retrieve(db, query=name, composer_id=row.id, k=6)
    hits = list(retrieved.get("hits") or [])
    base = _card_from_local(db, name=name, kind=kind, row=row, hits=hits)
    try:
        ext = json.loads(row.external_ids_json or "{}")
        if not isinstance(ext, dict):
            ext = {}
    except json.JSONDecodeError:
        ext = {}
    summary_en = row.summary_en or (base.get("summary") if not _has_cjk(str(base.get("summary") or "")) else "") or ""
    summary_zh = row.summary_zh or (base.get("summary") if _has_cjk(str(base.get("summary") or "")) else "") or ""
    locale_default = "zh" if summary_zh or row.name_zh or _has_cjk(name) else "en"
    display_name = row.name_zh if locale_default == "zh" and row.name_zh else (row.name_en or row.name_zh or name)
    rich = bool(summary_en or summary_zh)
    return {
        **base,
        "display_name": display_name,
        "display_name_en": row.name_en or "",
        "display_name_zh": row.name_zh or "",
        "summary": summary_zh if locale_default == "zh" and summary_zh else (summary_en or summary_zh),
        "summary_en": summary_en,
        "summary_zh": summary_zh,
        "summary_en_origin": str(ext.get("summary_en_origin") or ("local" if summary_en else "")),
        "summary_zh_origin": str(ext.get("summary_zh_origin") or ("local" if summary_zh else "")),
        "sources": [],
        "locale_default": locale_default,
        "source": "knowledge" if rich else base.get("source") or "unresolved",
        "matched": True,
        "aggregation": {"strategy": "field-merge", "revision": AGG_VERSION, "from": "local"},
    }


def aggregate_person_card(
    db: Session,
    *,
    name: str,
    kind: str = "person",
    fragments: list[dict[str, Any]] | None = None,
    fetch_remote: bool = True,
    persist: bool = True,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    clean = (name or "").strip()
    if not clean:
        raise ValueError("name required")
    kind_norm = (kind or "person").strip().lower() or "person"
    if kind_norm not in {"composer", "performer", "ensemble", "person"}:
        kind_norm = "person"

    row = find_local_person(db, clean)
    collected: list[dict[str, Any]] = []
    local_frag = fragment_from_local(row, name=clean, kind=kind_norm)
    if local_frag:
        collected.append(local_frag)

    for raw in fragments or []:
        if not isinstance(raw, dict):
            continue
        sid = str(raw.get("source_id") or "")
        if sid == "discogs" or raw.get("authority") == "discogs":
            collected.append(fragment_from_discogs_payload(raw))
        else:
            collected.append(raw)

    own = client is None
    http = client or httpx.Client(timeout=25.0, headers={"User-Agent": UA}, follow_redirects=True)
    try:
        if fetch_remote:
            # Prefer searching with best Latin/CJK label we already know
            search_name = clean
            for f in collected:
                if f.get("display_name_en") and not _has_cjk(str(f["display_name_en"])):
                    search_name = str(f["display_name_en"])
                    break
            # If query is CJK and Discogs gave Latin, use Latin for Wikidata
            try:
                collected.extend(fetch_wikidata_wikipedia_fragments(http, name=search_name, db=db))
                if search_name != clean and _has_cjk(clean):
                    # also try original CJK for ZH sitelinks / match
                    extra = fetch_wikidata_wikipedia_fragments(http, name=clean, db=db)
                    # only add if same QID or empty so far
                    have_qid = next((f.get("external_ids", {}).get("wikidata") for f in collected if f.get("source_id") == "wikidata"), None)
                    for ef in extra:
                        if ef.get("source_id") == "wikidata":
                            eq = (ef.get("external_ids") or {}).get("wikidata")
                            if have_qid and eq and eq != have_qid:
                                continue
                        if ef.get("source_id") == "wikipedia" and ef.get("lang") == "zh":
                            if not any(x.get("source_id") == "wikipedia" and x.get("lang") == "zh" for x in collected):
                                collected.append(ef)
            except Exception as exc:  # noqa: BLE001
                logger.warning("aggregate_remote_fetch_failed name=%s err=%s", clean, exc)
    finally:
        if own:
            http.close()

    # Drop remote fragments that fail identity vs query / discogs latin name
    identity_anchors = [clean]
    for f in collected:
        for key in ("display_name_en", "display_name_zh"):
            if f.get(key):
                identity_anchors.append(str(f[key]))
    filtered: list[dict[str, Any]] = []
    for f in collected:
        if f.get("source_id") in {"local", "discogs"}:
            filtered.append(f)
            continue
        label = _pick(str(f.get("display_name_en") or ""), str(f.get("display_name_zh") or ""))
        if not label:
            filtered.append(f)
            continue
        ok = any(
            names_compatible(a, label) or _norm(a) == _norm(label) or (_has_cjk(a) and _norm(a) == _norm(str(f.get("display_name_zh") or "")))
            for a in identity_anchors
            if a
        )
        # Wikidata search already identity-filtered; keep if QID present and discogs/local anchors exist
        if not ok and f.get("source_id") == "wikidata" and any(x.get("source_id") == "discogs" for x in collected):
            ok = True
        if not ok and f.get("source_id") == "wikipedia":
            ok = any(x.get("source_id") == "wikidata" for x in collected)
        if ok:
            filtered.append(f)
        else:
            logger.info("aggregate_drop_fragment source=%s label=%s query=%s", f.get("source_id"), label, clean)

    card = merge_fragments(name=clean, kind=kind_norm, fragments=filtered)
    if card.get("source") == "unresolved":
        return card
    if persist:
        card = persist_bilingual_card(db, card)
    return card
