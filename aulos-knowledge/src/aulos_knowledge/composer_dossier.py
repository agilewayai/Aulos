"""REQ-010 — Composer life dossier: Wikidata claims + SPARQL works → timeline + tree."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from aulos_knowledge.artifacts import write_artifact
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import (
    ComposerEntity,
    ComposerLifeEvent,
    FetchArtifact,
    FetchJob,
    KnowledgeChunk,
    KnowledgeDocument,
    MediaAsset,
    SourceAuthority,
    WorkEntity,
)
from aulos_knowledge.famous_composers import famous_by_id
from aulos_knowledge.fetch_policy import assert_url_allowed, throttle
from aulos_knowledge.media_fetch import fetch_wikidata_media_claims
from aulos_knowledge.publish_policy import document_status_for_source

logger = logging.getLogger("aulos_knowledge.composer_dossier")

EXTRACTOR_VERSION = "wikidata-dossier/0.1.0"
UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
ENTITY_DATA = "https://www.wikidata.org/wiki/Special:EntityData"
WORKS_CAP = 80
AWARDS_CAP = 12
POSITIONS_CAP = 16
RESIDENCE_CAP = 12
EDUCATION_CAP = 8

EVENT_TYPES = frozenset(
    {
        "birth",
        "death",
        "baptism",
        "education",
        "appointment",
        "residence",
        "marriage",
        "travel",
        "premiere",
        "composition_milestone",
        "other",
    }
)

# claim property → (event_type, title template, significance, cap)
CLAIM_EVENT_MAP: list[tuple[str, str, str, str, int | None]] = [
    ("P569", "birth", "Born", "major", 1),
    ("P570", "death", "Died", "major", 1),
    ("P69", "education", "Educated at", "minor", EDUCATION_CAP),
    ("P39", "appointment", "Held position", "minor", POSITIONS_CAP),
    ("P551", "residence", "Lived in", "minor", RESIDENCE_CAP),
    ("P26", "marriage", "Married", "minor", 4),
    ("P166", "other", "Award", "minor", AWARDS_CAP),
]


def _slug(text: str, *, max_len: int = 48) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return (s or "event")[:max_len]


def _time_to_date(time_val: dict[str, Any] | None) -> str:
    """Normalize Wikidata time value to YYYY / YYYY-MM / YYYY-MM-DD."""
    if not time_val or not isinstance(time_val, dict):
        return ""
    raw = str(time_val.get("time") or "")
    if not raw:
        return ""
    # +1685-03-21T00:00:00Z or -0500-00-00T00:00:00Z
    m = re.match(r"^([+-])(\d{4})-(\d{2})-(\d{2})", raw)
    if not m:
        return ""
    sign, year, month, day = m.group(1), m.group(2), m.group(3), m.group(4)
    if sign == "-":
        year = f"-{year}"
    precision = int(time_val.get("precision") or 11)
    if precision <= 9:  # year
        return year
    if precision == 10:  # month
        return f"{year}-{month}" if month != "00" else year
    if day == "00":
        return f"{year}-{month}" if month != "00" else year
    return f"{year}-{month}-{day}"


def _claim_mainsnak(claim: dict[str, Any]) -> dict[str, Any]:
    return (claim or {}).get("mainsnak") or {}


def _datavalue(claim: dict[str, Any]) -> Any:
    return (_claim_mainsnak(claim).get("datavalue") or {}).get("value")


def _entity_qid_from_claim(claim: dict[str, Any]) -> str:
    val = _datavalue(claim)
    if isinstance(val, dict) and val.get("id"):
        return str(val["id"])
    return ""


def _time_from_claim(claim: dict[str, Any]) -> str:
    val = _datavalue(claim)
    if isinstance(val, dict) and "time" in val:
        return _time_to_date(val)
    # qualifier P580 / P582
    quals = claim.get("qualifiers") or {}
    for prop in ("P580", "P585", "P582"):
        for q in quals.get(prop) or []:
            dv = ((q or {}).get("datavalue") or {}).get("value")
            if isinstance(dv, dict) and "time" in dv:
                return _time_to_date(dv)
    return ""


def _qualifier_time_range(claim: dict[str, Any]) -> tuple[str, str]:
    quals = claim.get("qualifiers") or {}
    start = end = ""
    for q in quals.get("P580") or []:
        dv = ((q or {}).get("datavalue") or {}).get("value")
        if isinstance(dv, dict):
            start = _time_to_date(dv)
            break
    for q in quals.get("P582") or []:
        dv = ((q or {}).get("datavalue") or {}).get("value")
        if isinstance(dv, dict):
            end = _time_to_date(dv)
            break
    if not start:
        start = _time_from_claim(claim)
    return start, end


def _label_from_entity(entity: dict[str, Any], lang: str = "en") -> str:
    labels = entity.get("labels") or {}
    if lang in labels:
        return str((labels[lang] or {}).get("value") or "")
    if "en" in labels:
        return str((labels["en"] or {}).get("value") or "")
    for v in labels.values():
        return str((v or {}).get("value") or "")
    return ""


def _lifespan(birth: str, death: str) -> str:
    by = birth[:4] if birth else ""
    dy = death[:4] if death else ""
    if by and dy:
        return f"{by}–{dy}"
    return by or dy or ""


def fetch_entity_json(
    client: httpx.Client,
    *,
    source: SourceAuthority,
    qid: str,
) -> dict[str, Any]:
    url = f"{ENTITY_DATA}/{qid}.json"
    assert_url_allowed(source, url)
    throttle(source)
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()


def fetch_sparql_works(
    client: httpx.Client,
    *,
    source: SourceAuthority,
    composer_qid: str,
    limit: int = WORKS_CAP,
) -> list[dict[str, Any]]:
    """Works with P86 = composer; optional inception, genre, part-of."""
    q = f"""
SELECT ?work ?workLabel ?inception ?genreLabel ?partOf ?partOfLabel ?catalog WHERE {{
  ?work wdt:P86 wd:{composer_qid} .
  OPTIONAL {{ ?work wdt:P571 ?inception }}
  OPTIONAL {{ ?work wdt:P136 ?genre }}
  OPTIONAL {{ ?work wdt:P361 ?partOf }}
  OPTIONAL {{ ?work wdt:P528 ?catalog }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh" }}
}}
LIMIT {int(limit)}
"""
    assert_url_allowed(source, SPARQL_ENDPOINT)
    throttle(source)
    resp = client.get(
        SPARQL_ENDPOINT,
        params={"query": q, "format": "json"},
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA},
    )
    resp.raise_for_status()
    bindings = ((resp.json().get("results") or {}).get("bindings") or [])
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for b in bindings:
        work_uri = ((b.get("work") or {}).get("value") or "")
        wqid = work_uri.rsplit("/", 1)[-1] if work_uri else ""
        if not wqid or wqid in seen:
            continue
        seen.add(wqid)
        part_uri = ((b.get("partOf") or {}).get("value") or "")
        pqid = part_uri.rsplit("/", 1)[-1] if part_uri else ""
        inception = ((b.get("inception") or {}).get("value") or "")
        year = ""
        if inception:
            m = re.match(r"^(\d{4})", inception)
            year = m.group(1) if m else inception[:4]
        out.append(
            {
                "qid": wqid,
                "title_en": ((b.get("workLabel") or {}).get("value") or wqid),
                "year_start": year,
                "genre": ((b.get("genreLabel") or {}).get("value") or ""),
                "parent_qid": pqid if pqid.startswith("Q") else "",
                "parent_label": ((b.get("partOfLabel") or {}).get("value") or ""),
                "catalog": ((b.get("catalog") or {}).get("value") or ""),
            }
        )
    return out


def _resolve_place_labels(
    client: httpx.Client,
    *,
    source: SourceAuthority,
    qids: list[str],
) -> dict[str, str]:
    labels: dict[str, str] = {}
    uniq = [q for q in dict.fromkeys(qids) if q.startswith("Q")][:40]
    for qid in uniq:
        try:
            data = fetch_entity_json(client, source=source, qid=qid)
            ent = (data.get("entities") or {}).get(qid) or {}
            labels[qid] = _label_from_entity(ent) or qid
        except Exception as exc:  # noqa: BLE001
            logger.warning("place_label_failed qid=%s err=%s", qid, exc)
            labels[qid] = qid
    return labels


def extract_life_events(
    *,
    composer_id: str,
    qid: str,
    claims: dict[str, Any],
    place_labels: dict[str, str],
    source_id: str,
    artifact_id: int | None,
    job_id: int | None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    birth_place = ""
    death_place = ""
    for c in claims.get("P19") or []:
        birth_place = _entity_qid_from_claim(c)
        break
    for c in claims.get("P20") or []:
        death_place = _entity_qid_from_claim(c)
        break

    for prop, event_type, title_prefix, significance, cap in CLAIM_EVENT_MAP:
        claims_list = list(claims.get(prop) or [])
        if cap is not None:
            claims_list = claims_list[:cap]
        for claim in claims_list:
            if prop in ("P569", "P570"):
                date_start = _time_from_claim(claim)
                date_end = ""
                place_qid = birth_place if prop == "P569" else death_place
                place_label = place_labels.get(place_qid, "")
                title = title_prefix
                if place_label:
                    title = f"{title_prefix} in {place_label}"
                ext = {"wikidata_prop": prop, "composer_qid": qid}
            else:
                target = _entity_qid_from_claim(claim)
                date_start, date_end = _qualifier_time_range(claim)
                place_qid = target if prop in ("P551", "P69") else ""
                place_label = place_labels.get(target, target) if target else ""
                title = f"{title_prefix} {place_label}".strip() if place_label else title_prefix
                ext = {"wikidata_prop": prop, "target_qid": target, "composer_qid": qid}

            if not date_start and event_type not in ("birth", "death"):
                # Still keep undated major appointments lightly; skip empty undated noise
                if event_type in ("other", "residence", "education") and not place_label:
                    continue

            eid = f"{composer_id}:{event_type}:{date_start or 'undated'}:{_slug(title)}"
            events.append(
                {
                    "id": eid[:220],
                    "composer_id": composer_id,
                    "event_type": event_type if event_type in EVENT_TYPES else "other",
                    "title_en": title[:512],
                    "title_zh": "",
                    "description": "",
                    "date_start": date_start,
                    "date_end": date_end,
                    "place_label": place_label[:255],
                    "place_qid": place_qid[:32],
                    "significance": significance,
                    "external_ids_json": json.dumps(ext, ensure_ascii=False),
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "job_id": job_id,
                    "sort_key": date_start or "9999",
                }
            )

    # P800 notable works → composition milestones (when dated)
    for claim in list(claims.get("P800") or [])[:20]:
        wqid = _entity_qid_from_claim(claim)
        date_start, date_end = _qualifier_time_range(claim)
        if not date_start:
            continue
        title = f"Notable work {wqid}"
        eid = f"{composer_id}:composition_milestone:{date_start}:{_slug(wqid)}"
        events.append(
            {
                "id": eid[:220],
                "composer_id": composer_id,
                "event_type": "composition_milestone",
                "title_en": title[:512],
                "title_zh": "",
                "description": "",
                "date_start": date_start,
                "date_end": date_end,
                "place_label": "",
                "place_qid": "",
                "significance": "major",
                "external_ids_json": json.dumps(
                    {"wikidata_prop": "P800", "work_qid": wqid, "composer_qid": qid},
                    ensure_ascii=False,
                ),
                "source_id": source_id,
                "artifact_id": artifact_id,
                "job_id": job_id,
                "sort_key": date_start,
            }
        )

    # Deduplicate by id
    by_id: dict[str, dict[str, Any]] = {}
    for ev in events:
        by_id[ev["id"]] = ev
    return list(by_id.values())


def _work_row_id(qid: str) -> str:
    return f"wd:{qid}"


def upsert_works_tree(
    db: Session,
    *,
    composer_id: str,
    works: list[dict[str, Any]],
) -> list[WorkEntity]:
    # First pass: ensure parent stubs exist
    parent_qids = {w["parent_qid"] for w in works if w.get("parent_qid")}
    work_qids = {w["qid"] for w in works}
    for pqid in parent_qids - work_qids:
        parent = next((w for w in works if w.get("parent_qid") == pqid), None)
        label = ""
        for w in works:
            if w.get("parent_qid") == pqid:
                label = w.get("parent_label") or pqid
                break
        works.append(
            {
                "qid": pqid,
                "title_en": label or pqid,
                "year_start": "",
                "genre": "",
                "parent_qid": "",
                "parent_label": "",
                "catalog": "",
                "_stub": True,
            }
        )

    children_of: set[str] = set()
    for w in works:
        if w.get("parent_qid"):
            children_of.add(w["parent_qid"])

    rows: list[WorkEntity] = []
    for w in works:
        wid = _work_row_id(w["qid"])
        row = db.get(WorkEntity, wid)
        if row is None:
            row = WorkEntity(id=wid, composer_id=composer_id)
            db.add(row)
        row.composer_id = composer_id
        row.title_en = str(w.get("title_en") or row.title_en or w["qid"])
        parent_qid = w.get("parent_qid") or ""
        row.parent_work_id = _work_row_id(parent_qid) if parent_qid else None
        if w["qid"] in children_of:
            row.work_kind = "collection"
        elif parent_qid:
            row.work_kind = "movement"
        else:
            row.work_kind = "work"
        row.year_start = str(w.get("year_start") or "")
        catalogs = []
        if w.get("catalog"):
            catalogs.append(str(w["catalog"]))
        try:
            existing = json.loads(row.catalog_numbers_json or "[]")
            if isinstance(existing, list):
                for c in existing:
                    if c not in catalogs:
                        catalogs.append(c)
        except json.JSONDecodeError:
            pass
        row.catalog_numbers_json = json.dumps(catalogs, ensure_ascii=False)
        facets = {}
        try:
            facets = json.loads(row.facets_json or "{}")
        except json.JSONDecodeError:
            facets = {}
        if w.get("genre"):
            facets["genre"] = w["genre"]
        row.facets_json = json.dumps(facets, ensure_ascii=False)
        ext = {}
        try:
            ext = json.loads(row.external_ids_json or "{}")
        except json.JSONDecodeError:
            ext = {}
        ext["wikidata"] = w["qid"]
        row.external_ids_json = json.dumps(ext, ensure_ascii=False)
        rows.append(row)
    db.flush()
    return rows


def upsert_life_events(db: Session, events: list[dict[str, Any]]) -> list[ComposerLifeEvent]:
    rows: list[ComposerLifeEvent] = []
    for ev in events:
        row = db.get(ComposerLifeEvent, ev["id"])
        if row is None:
            row = ComposerLifeEvent(id=ev["id"], composer_id=ev["composer_id"])
            db.add(row)
        for key in (
            "composer_id",
            "event_type",
            "title_en",
            "title_zh",
            "description",
            "date_start",
            "date_end",
            "place_label",
            "place_qid",
            "significance",
            "external_ids_json",
            "source_id",
            "artifact_id",
            "job_id",
            "sort_key",
        ):
            setattr(row, key, ev[key])
        rows.append(row)
    db.flush()
    return rows


def _write_timeline_docs(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    art: FetchArtifact,
    composer_id: str,
    label_en: str,
    events: list[dict[str, Any]],
    works: list[dict[str, Any]],
) -> None:
    lines = [f"Composer timeline: {label_en}", ""]
    for ev in sorted(events, key=lambda e: e.get("sort_key") or "9999"):
        lines.append(
            f"{ev.get('date_start') or '?'} — {ev.get('title_en')} "
            f"[{ev.get('event_type')}] {ev.get('place_label') or ''}".strip()
        )
    body = "\n".join(lines)
    doc = KnowledgeDocument(
        title=f"Timeline — {label_en}",
        entity_type="composer_timeline",
        entity_id=composer_id,
        aulos_work_id="",
        body=body,
        status=document_status_for_source(source),
        source_id=source.id,
        artifact_id=art.id,
        job_id=job.id,
        extractor_version=EXTRACTOR_VERSION,
        license_class=source.license_class,
    )
    db.add(doc)
    db.flush()
    db.add(
        KnowledgeChunk(
            document_id=doc.id,
            section="composer_timeline",
            text=body[:8000],
            aulos_work_id="",
        )
    )

    for w in works[:40]:
        if w.get("_stub"):
            continue
        wid = _work_row_id(w["qid"])
        wbody = (
            f"{w.get('title_en')} ({w.get('year_start') or 'n/a'})\n"
            f"Genre: {w.get('genre') or 'n/a'}\n"
            f"Catalog: {w.get('catalog') or 'n/a'}\n"
            f"Wikidata: {w['qid']}"
        )
        wdoc = KnowledgeDocument(
            title=str(w.get("title_en") or wid),
            entity_type="work",
            entity_id=wid,
            aulos_work_id="",
            body=wbody,
            status=document_status_for_source(source),
            source_id=source.id,
            artifact_id=art.id,
            job_id=job.id,
            extractor_version=EXTRACTOR_VERSION,
            license_class=source.license_class,
        )
        db.add(wdoc)
        db.flush()
        db.add(
            KnowledgeChunk(
                document_id=wdoc.id,
                section="work",
                text=wbody,
                aulos_work_id="",
            )
        )


def run_composer_dossier(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    """Wikidata connector mode=composer_dossier."""
    composer_id = str(params.get("composer_id") or "").strip()
    qid = str(params.get("qid") or params.get("wikidata_qid") or "").strip().upper()
    if not qid:
        qids = params.get("qids") or []
        if isinstance(qids, str):
            qids = [qids]
        if qids:
            qid = str(qids[0]).strip().upper()
    if not composer_id and qid:
        famous = famous_by_id()
        for entry in famous.values():
            if entry.get("wikidata_qid") == qid:
                composer_id = entry["composer_id"]
                break
        if not composer_id:
            composer_id = qid.lower()
    if not qid:
        raise ValueError("composer_dossier requires qid / wikidata_qid")
    if not composer_id:
        raise ValueError("composer_dossier requires composer_id")

    settings = get_settings()
    with httpx.Client(timeout=60.0, headers={"User-Agent": UA}) as client:
        entity_payload = fetch_entity_json(client, source=source, qid=qid)
        entity = (entity_payload.get("entities") or {}).get(qid) or {}
        claims = entity.get("claims") or {}

        place_qids: list[str] = []
        for prop in ("P19", "P20", "P69", "P39", "P551", "P26", "P166"):
            for claim in claims.get(prop) or []:
                t = _entity_qid_from_claim(claim)
                if t:
                    place_qids.append(t)
        place_labels = _resolve_place_labels(client, source=source, qids=place_qids)

        works_raw = fetch_sparql_works(client, source=source, composer_qid=qid, limit=WORKS_CAP)

        # Prefer P800 notable works first in ordering
        notable: set[str] = set()
        for claim in claims.get("P800") or []:
            nq = _entity_qid_from_claim(claim)
            if nq:
                notable.add(nq)
        works_raw.sort(key=lambda w: (0 if w["qid"] in notable else 1, w.get("title_en") or ""))

        bundle = {
            "mode": "composer_dossier",
            "qid": qid,
            "composer_id": composer_id,
            "entity": entity_payload,
            "works": works_raw,
            "place_labels": place_labels,
        }
        payload = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
        digest, rel, _ = write_artifact(
            root=Path(settings.artifact_root),
            source_id=source.id,
            job_id=job.id,
            payload=payload,
            suffix="json",
        )
        art = FetchArtifact(
            job_id=job.id,
            source_id=source.id,
            content_hash=digest,
            content_type="application/json",
            storage_path=rel,
            source_url=f"{ENTITY_DATA}/{qid}.json",
            byte_size=len(payload),
        )
        db.add(art)
        db.flush()

        labels = entity.get("labels") or {}
        label_en = (labels.get("en") or {}).get("value") or qid
        label_zh = (labels.get("zh-hans") or labels.get("zh") or {}).get("value") or ""
        desc_en = ((entity.get("descriptions") or {}).get("en") or {}).get("value") or ""
        desc_zh = (
            ((entity.get("descriptions") or {}).get("zh-hans") or {}).get("value")
            or ((entity.get("descriptions") or {}).get("zh") or {}).get("value")
            or ""
        )
        sitelinks = entity.get("sitelinks") or {}
        enwiki = (sitelinks.get("enwiki") or {}).get("title") or ""
        zhwiki = (sitelinks.get("zhwiki") or {}).get("title") or ""

        birth = ""
        death = ""
        for c in claims.get("P569") or []:
            birth = _time_from_claim(c)
            break
        for c in claims.get("P570") or []:
            death = _time_from_claim(c)
            break

        famous = famous_by_id().get(composer_id) or {}
        era = str(famous.get("era") or "")

        row = db.get(ComposerEntity, composer_id)
        if row is None:
            row = ComposerEntity(id=composer_id)
            db.add(row)
        row.name_en = label_en or row.name_en
        row.name_zh = label_zh or row.name_zh
        row.lifespan = _lifespan(birth, death) or row.lifespan
        row.era = era or row.era
        row.summary_en = desc_en or row.summary_en
        row.summary_zh = desc_zh or row.summary_zh
        ext: dict[str, Any] = {}
        try:
            ext = json.loads(row.external_ids_json or "{}")
        except json.JSONDecodeError:
            ext = {}
        ext["wikidata"] = qid
        if enwiki:
            ext["enwiki"] = enwiki
        if zhwiki:
            ext["zhwiki"] = zhwiki
        row.external_ids_json = json.dumps(ext, ensure_ascii=False)

        events = extract_life_events(
            composer_id=composer_id,
            qid=qid,
            claims=claims,
            place_labels=place_labels,
            source_id=source.id,
            artifact_id=art.id,
            job_id=job.id,
        )
        # Enrich P800 titles from works list
        work_titles = {w["qid"]: w.get("title_en") for w in works_raw}
        for ev in events:
            if ev["event_type"] == "composition_milestone":
                try:
                    eids = json.loads(ev["external_ids_json"] or "{}")
                except json.JSONDecodeError:
                    eids = {}
                wqid = eids.get("work_qid") or ""
                if wqid and work_titles.get(wqid):
                    ev["title_en"] = f"Notable work: {work_titles[wqid]}"

        upsert_life_events(db, events)
        upsert_works_tree(db, composer_id=composer_id, works=works_raw)
        _write_timeline_docs(
            db,
            source=source,
            job=job,
            art=art,
            composer_id=composer_id,
            label_en=label_en,
            events=events,
            works=works_raw,
        )

        fetch_wikidata_media_claims(
            db,
            source=source,
            job=job,
            qid=qid,
            claims=claims,
            composer_id=composer_id,
            aulos_work_id="",
        )

        # Fan-out Wikipedia narrative (async child — does not block dossier success)
        if enwiki or zhwiki:
            try:
                from aulos_knowledge.jobs import enqueue_and_maybe_run

                wiki_src = db.get(SourceAuthority, "wikipedia")
                if wiki_src and wiki_src.enabled:
                    title = enwiki or zhwiki
                    langs = []
                    if enwiki:
                        langs.append("en")
                    if zhwiki:
                        langs.append("zh")
                    enqueue_and_maybe_run(
                        db,
                        source_id="wikipedia",
                        params={
                            "title": title,
                            "langs": langs or ["en"],
                            "composer_id": composer_id,
                        },
                        sync=False,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("wikipedia_fanout_failed composer=%s err=%s", composer_id, exc)

    db.commit()


def _portrait_meta(db: Session, composer_id: str) -> dict[str, Any] | None:
    row = (
        db.query(MediaAsset)
        .filter(MediaAsset.entity_id == composer_id, MediaAsset.kind == "image")
        .order_by(MediaAsset.id.desc())
        .first()
    )
    if not row:
        return None
    return {
        "media_id": row.id,
        "title": row.title,
        "content_type": row.content_type,
        "license_class": row.license_class,
        "source_url": row.source_url,
        "content_path": f"/v1/admin/media/{row.id}/content",
    }


def _build_works_tree(works: list[WorkEntity]) -> list[dict[str, Any]]:
    by_id = {w.id: w for w in works}
    children: dict[str | None, list[WorkEntity]] = {}
    for w in works:
        parent = w.parent_work_id if w.parent_work_id in by_id else None
        children.setdefault(parent, []).append(w)

    def node(w: WorkEntity) -> dict[str, Any]:
        try:
            catalogs = json.loads(w.catalog_numbers_json or "[]")
        except json.JSONDecodeError:
            catalogs = []
        try:
            facets = json.loads(w.facets_json or "{}")
        except json.JSONDecodeError:
            facets = {}
        kids = [node(c) for c in sorted(children.get(w.id) or [], key=lambda x: x.title_en or x.id)]
        return {
            "id": w.id,
            "title_en": w.title_en,
            "title_zh": w.title_zh,
            "work_kind": w.work_kind or "work",
            "year_start": w.year_start or "",
            "year_end": w.year_end or "",
            "catalog_numbers": catalogs,
            "facets": facets,
            "children": kids,
        }

    roots = children.get(None) or []
    return [node(w) for w in sorted(roots, key=lambda x: (x.year_start or "9999", x.title_en or x.id))]


def build_composer_dossier(db: Session, composer_id: str) -> dict[str, Any] | None:
    """Assemble API payload for GET .../dossier."""
    row = db.get(ComposerEntity, composer_id)
    famous = famous_by_id().get(composer_id)
    if row is None and famous is None:
        return None

    name_en = (row.name_en if row else "") or (famous or {}).get("name_en") or composer_id
    name_zh = (row.name_zh if row else "") or (famous or {}).get("name_zh") or ""
    lifespan = (row.lifespan if row else "") or ""
    era = (row.era if row else "") or (famous or {}).get("era") or ""
    summary_en = (row.summary_en if row else "") or ""
    summary_zh = (row.summary_zh if row else "") or ""
    ext: dict[str, Any] = {}
    if row:
        try:
            ext = json.loads(row.external_ids_json or "{}")
        except json.JSONDecodeError:
            ext = {}
    if famous and not ext.get("wikidata"):
        ext["wikidata"] = famous.get("wikidata_qid")

    events = (
        db.query(ComposerLifeEvent)
        .filter(ComposerLifeEvent.composer_id == composer_id)
        .order_by(ComposerLifeEvent.sort_key, ComposerLifeEvent.id)
        .all()
    )
    timeline = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "title_en": e.title_en,
            "title_zh": e.title_zh,
            "description": e.description,
            "date_start": e.date_start,
            "date_end": e.date_end,
            "place_label": e.place_label,
            "place_qid": e.place_qid,
            "significance": e.significance,
            "sort_key": e.sort_key,
        }
        for e in events
    ]

    works = db.query(WorkEntity).filter(WorkEntity.composer_id == composer_id).all()
    works_tree = _build_works_tree(works)

    doc_count = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.entity_id == composer_id)
        .count()
    )
    work_doc_count = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.entity_type == "work")
        .filter(KnowledgeDocument.entity_id.like("wd:%"))
        .count()
        if works
        else 0
    )

    return {
        "composer": {
            "id": composer_id,
            "name_en": name_en,
            "name_zh": name_zh,
            "lifespan": lifespan,
            "era": era,
            "summary_en": summary_en,
            "summary_zh": summary_zh,
            "external_ids": ext,
            "famous": bool(famous),
        },
        "portrait": _portrait_meta(db, composer_id),
        "timeline": timeline,
        "works_tree": works_tree,
        "works_count": len(works),
        "events_count": len(timeline),
        "doc_counts": {
            "composer": doc_count,
            "works": work_doc_count,
        },
    }


def resolve_composer_qid(db: Session, composer_id: str, qid_hint: str = "") -> str:
    if qid_hint:
        return qid_hint.strip().upper()
    famous = famous_by_id().get(composer_id)
    if famous and famous.get("wikidata_qid"):
        return str(famous["wikidata_qid"]).upper()
    row = db.get(ComposerEntity, composer_id)
    if row:
        try:
            ext = json.loads(row.external_ids_json or "{}")
        except json.JSONDecodeError:
            ext = {}
        q = str(ext.get("wikidata") or ext.get("wikidata_qid") or "")
        if q:
            return q.upper()
    return ""
