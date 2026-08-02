"""Discogs release fetch + generic classical credit analysis (SPEC-008).

No composer/work hardcoding — role heuristics + Catalog identity downstream.
OPS stores personal user token under SystemSetting `discogs.api` (see /v1/ops/discogs).
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger("aulos_api.discogs")

_UA = "AulosListeningBot/0.1 (+https://aulos.purezen.ai; classical listening guides)"
_API = "https://api.discogs.com"
DISCOGS_SETTING_KEY = "discogs.api"

_COMPOSER_ROLE = re.compile(
    r"(?i)\b(compos(er|ed|ition)?|written[\s-]?by|music[\s-]?by)\b"
)
_PERFORMER_ROLE = re.compile(
    r"(?i)\b(piano|violin|cello|viola|flute|oboe|clarinet|bassoon|horn|trumpet|"
    r"trombone|organ|harpsichord|guitar|voice|soprano|alto|tenor|bass|choir|"
    r"orchestra|ensemble|quartet|trio|conductor|directed|performed|soloist|"
    r"mezzo|baritone|countertenor|harp|percussion|timpani)\b"
)
_ENSEMBLE_ROLE = re.compile(
    r"(?i)\b(orchestra|ensemble|choir|chorus|philharmonic|symphony|quartet|trio|quintet)\b"
)
_ARTIST_PREFIX = re.compile(
    r"^(?P<artist>.+?)\s*[-–—:]\s*(?P<title>.+)$"
)


class DiscogsError(Exception):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def load_discogs_config(db: Session) -> dict[str, Any]:
    from aulos_api.db.models import SystemSetting

    row = db.query(SystemSetting).filter(SystemSetting.key == DISCOGS_SETTING_KEY).one_or_none()
    data: dict[str, Any] = {}
    if row and row.value:
        try:
            parsed = json.loads(row.value)
            if isinstance(parsed, dict):
                data = parsed
        except json.JSONDecodeError:
            data = {}
    return {
        "user_token": str(data.get("user_token") or ""),
        "enabled": bool(data.get("enabled", True)),
    }


def public_discogs_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    c = cfg or {}
    env_token = bool((os.environ.get("AULOS_DISCOGS_TOKEN") or "").strip())
    env_key = bool(
        (os.environ.get("AULOS_DISCOGS_KEY") or "").strip()
        and (os.environ.get("AULOS_DISCOGS_SECRET") or "").strip()
    )
    ops_token = bool(c.get("user_token"))
    return {
        "enabled": bool(c.get("enabled", True)),
        "user_token_set": ops_token,
        "auth_source": (
            "ops" if ops_token else ("env_token" if env_token else ("env_key" if env_key else "none"))
        ),
        "authenticated": bool(ops_token or env_token or env_key),
    }


def save_discogs_config(
    db: Session,
    *,
    user_token: str | None = None,
    clear_user_token: bool = False,
    enabled: bool | None = None,
) -> dict[str, Any]:
    from aulos_api.db.models import SystemSetting

    current = load_discogs_config(db)
    if enabled is not None:
        current["enabled"] = bool(enabled)
    if clear_user_token:
        current["user_token"] = ""
    elif user_token is not None:
        # Blank string without clear keeps existing (OPS leave-blank-to-keep).
        trimmed = user_token.strip()
        if trimmed:
            current["user_token"] = trimmed
    payload = json.dumps(
        {"user_token": current["user_token"], "enabled": current["enabled"]},
        ensure_ascii=False,
    )
    row = db.query(SystemSetting).filter(SystemSetting.key == DISCOGS_SETTING_KEY).one_or_none()
    if row is None:
        db.add(SystemSetting(key=DISCOGS_SETTING_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    return public_discogs_config(current)


def _auth_params(db: Session | None = None) -> dict[str, str]:
    """Prefer OPS-stored personal token, then env token / key+secret."""
    if db is not None:
        try:
            cfg = load_discogs_config(db)
            if not cfg.get("enabled", True):
                return {}
            token = str(cfg.get("user_token") or "").strip()
            if token:
                return {"token": token}
        except Exception as exc:  # noqa: BLE001
            logger.warning("discogs_ops_config_failed err=%s", exc)
    token = (os.environ.get("AULOS_DISCOGS_TOKEN") or "").strip()
    if token:
        return {"token": token}
    key = (os.environ.get("AULOS_DISCOGS_KEY") or "").strip()
    secret = (os.environ.get("AULOS_DISCOGS_SECRET") or "").strip()
    if key and secret:
        return {"key": key, "secret": secret}
    return {}


def fetch_discogs_entity(
    entity_id: int | str,
    *,
    client: httpx.Client | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """Fetch release by id; on 404 try master. Returns normalized payload + raw."""
    rid = str(entity_id).strip()
    if not rid.isdigit():
        raise DiscogsError("Invalid Discogs id", status_code=400)

    if db is not None:
        try:
            if not load_discogs_config(db).get("enabled", True):
                raise DiscogsError(
                    "Discogs connector disabled in OPS — enable under LLM → Discogs",
                    status_code=503,
                )
        except DiscogsError:
            raise
        except Exception:  # noqa: BLE001
            pass

    own = client is None
    http = client or httpx.Client(timeout=20.0, headers={"User-Agent": _UA}, follow_redirects=True)
    params = _auth_params(db)
    try:
        release = _get_json(http, f"{_API}/releases/{rid}", params=params)
        if release is not None:
            return {"kind": "release", "id": int(rid), "raw": release}
        master = _get_json(http, f"{_API}/masters/{rid}", params=params)
        if master is None:
            raise DiscogsError(f"Discogs release not found: {rid}", status_code=404)
        main_id = master.get("main_release")
        if main_id:
            main = _get_json(http, f"{_API}/releases/{main_id}", params=params)
            if main is not None:
                return {
                    "kind": "master",
                    "id": int(rid),
                    "main_release_id": int(main_id),
                    "raw": main,
                    "master_raw": master,
                }
        return {"kind": "master", "id": int(rid), "raw": master, "master_raw": master}
    except DiscogsError:
        raise
    except httpx.HTTPError as exc:
        logger.warning("discogs_http_failed id=%s err=%s", rid, exc)
        raise DiscogsError("Discogs unavailable", status_code=502) from exc
    finally:
        if own:
            http.close()


def _get_json(client: httpx.Client, url: str, *, params: dict[str, str]) -> dict[str, Any] | None:
    r = client.get(url, params=params or None)
    if r.status_code == 404:
        return None
    if r.status_code == 429:
        raise DiscogsError("Discogs rate limited — retry later or set AULOS_DISCOGS_TOKEN", status_code=502)
    if r.status_code >= 400:
        logger.warning("discogs_status url=%s status=%s body=%s", url, r.status_code, r.text[:200])
        raise DiscogsError(f"Discogs error ({r.status_code})", status_code=502)
    data = r.json()
    return data if isinstance(data, dict) else None


def _names(items: list[Any] | None) -> list[str]:
    out: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if name and name not in out:
            out.append(name)
    return out


def _role_names(extra: list[Any] | None, role_re: re.Pattern[str]) -> list[str]:
    out: list[str] = []
    for item in extra or []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        if not role_re.search(role):
            continue
        name = str(item.get("name") or "").strip()
        if name and name not in out:
            out.append(name)
    return out


_WORKISH_TITLE = re.compile(
    r"(?i)\b(concerto|sonata|symphony|quartet|trio|quintet|prelude|fugue|"
    r"nocturne|variations?|mass|requiem|suite|overture|rhapsody|impromptu|"
    r"mazurka|waltz|etude|étude|cantata|oratorio|partita|toccata)\b"
)


def _catno_variants(catno: str) -> list[str]:
    """Discogs catno spelling variants (DG: '423 287-1' vs '423-287-1')."""
    raw = re.sub(r"\s+", " ", (catno or "").strip())
    if not raw:
        return []
    out: list[str] = []
    spaced = raw.replace("-", " ").replace("–", " ").replace("—", " ")
    spaced = re.sub(r"\s+", " ", spaced).strip()
    # Prefer official DG-like: first gap space, rest keep last hyphen if 3 parts
    parts = re.split(r"[\s\-–—./]+", raw)
    parts = [p for p in parts if p]
    if len(parts) >= 3:
        dg = f"{parts[0]} {'-'.join(parts[1:])}"
        if dg not in out:
            out.append(dg)
    for v in (raw, spaced, raw.replace(" ", "-"), "-".join(parts)):
        if v and v not in out:
            out.append(v)
    return out


def _guess_work_title(raw: dict[str, Any], artists: list[str]) -> str:
    title = str(raw.get("title") or "").strip()
    m = _ARTIST_PREFIX.match(title)
    if m:
        title = m.group("title").strip()
    for artist in artists:
        if artist and title.lower().startswith(artist.lower()):
            title = title[len(artist) :].lstrip(" -–—:").strip()
    paren = re.search(r"\(([^)]{8,120})\)\s*$", title)
    paren_title = paren.group(1).strip() if paren else ""

    tracks = [
        str(t.get("title") or "").strip()
        for t in (raw.get("tracklist") or [])
        if isinstance(t, dict) and str(t.get("type_") or "track") != "heading"
    ]
    tracks = [t for t in tracks if t]

    # SPEC-033: multi catalog numbers → keep program-level shelf (do not collapse
    # to the single longest track / BWV). IntentLock / Catalog then see multi_work.
    multi_program = False
    try:
        import sys
        from pathlib import Path

        skills = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if skills.is_dir() and str(skills) not in sys.path:
            sys.path.insert(0, str(skills))
        from aulos_skills.identity_lock import extract_catalog_numbers

        catalog_blob = " ".join(x for x in (title, paren_title, *tracks) if x)
        if len(extract_catalog_numbers(catalog_blob)) >= 2:
            multi_program = True
    except Exception:  # noqa: BLE001
        multi_program = False

    if multi_program and title:
        picked = title[:160]
    else:
        candidates: list[str] = []
        for cand in (title, paren_title, *tracks):
            if cand and _WORKISH_TITLE.search(cand):
                candidates.append(cand)
        if candidates:
            # Prefer the richest classical title (release / paren often beat "Variation 1").
            candidates.sort(key=lambda s: (len(s), s), reverse=True)
            picked = candidates[0][:160]
        elif len(tracks) >= 2:
            prefix = os.path.commonprefix(tracks).rstrip(" :-–—0123456789.")
            if len(prefix) >= 8:
                picked = prefix[:160]
            else:
                picked = title[:160]
        elif tracks and (not title or title.lower() in {"classical", "various"}):
            picked = tracks[0][:160]
        else:
            picked = title[:160]

    # Packaging / multi-language dump → listening-work title (systemic)
    try:
        import sys
        from pathlib import Path

        skills = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if skills.is_dir() and str(skills) not in sys.path:
            sys.path.insert(0, str(skills))
        from aulos_skills.prose_hygiene import clean_packaging_work_title

        composers = [
            str(a.get("name") or "")
            for a in (raw.get("extraartists") or []) + (raw.get("artists") or [])
            if isinstance(a, dict)
        ]
        composer_hint = next((c for c in composers if c), "")
        return clean_packaging_work_title(picked, composer=composer_hint)
    except Exception:  # noqa: BLE001
        return picked


def search_discogs_by_catno(
    catno: str,
    *,
    client: httpx.Client | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """Resolve a catalog number to a release payload via Discogs database search."""
    variants = _catno_variants(catno)
    if not variants:
        raise DiscogsError("Invalid Discogs catalog number", status_code=400)

    if db is not None:
        try:
            if not load_discogs_config(db).get("enabled", True):
                raise DiscogsError(
                    "Discogs connector disabled in OPS — enable under Discogs tab",
                    status_code=503,
                )
        except DiscogsError:
            raise
        except Exception:  # noqa: BLE001
            pass

    own = client is None
    http = client or httpx.Client(timeout=20.0, headers={"User-Agent": _UA}, follow_redirects=True)
    auth = _auth_params(db)
    try:
        hits: list[dict[str, Any]] = []
        for variant in variants:
            data = _get_json(
                http,
                f"{_API}/database/search",
                params={**auth, "type": "release", "catno": variant, "per_page": "10"},
            )
            if not data:
                continue
            for row in data.get("results") or []:
                if isinstance(row, dict) and row.get("id"):
                    hits.append(row)
            if hits:
                break
        if not hits:
            # Fallback free-text q=
            for variant in variants:
                data = _get_json(
                    http,
                    f"{_API}/database/search",
                    params={**auth, "type": "release", "q": variant, "per_page": "10"},
                )
                if not data:
                    continue
                for row in data.get("results") or []:
                    if not isinstance(row, dict) or not row.get("id"):
                        continue
                    cat = str(row.get("catno") or "").lower().replace(" ", "")
                    needle = variant.lower().replace(" ", "").replace("-", "")
                    if needle and needle in cat.replace("-", ""):
                        hits.append(row)
                if hits:
                    break
        if not hits:
            raise DiscogsError(f"Discogs catalog number not found: {catno}", status_code=404)

        # Prefer Classical genre when present.
        classical = [h for h in hits if "Classical" in (h.get("genre") or [])]
        chosen = classical[0] if classical else hits[0]
        release_id = int(chosen["id"])
        payload = fetch_discogs_entity(release_id, client=http, db=db)
        payload["resolved_from"] = "catno"
        payload["catno_query"] = catno
        payload["catno_match"] = str(chosen.get("catno") or "")
        return payload
    except DiscogsError:
        raise
    except httpx.HTTPError as exc:
        logger.warning("discogs_catno_search_failed catno=%s err=%s", catno, exc)
        raise DiscogsError("Discogs unavailable", status_code=502) from exc
    finally:
        if own:
            http.close()


def _normalize_search_hit(row: dict[str, Any]) -> dict[str, Any] | None:
    rid = row.get("id")
    if rid is None:
        return None
    try:
        release_id = int(rid)
    except (TypeError, ValueError):
        return None
    labels = row.get("label") or []
    if isinstance(labels, str):
        label = labels
    elif isinstance(labels, list) and labels:
        label = str(labels[0])
    else:
        label = ""
    genres = [str(g) for g in (row.get("genre") or []) if g][:4]
    return {
        "id": release_id,
        "title": str(row.get("title") or "").strip(),
        "catno": str(row.get("catno") or "").strip(),
        "year": str(row.get("year") or "").strip(),
        "label": label.strip(),
        "country": str(row.get("country") or "").strip(),
        "thumb": str(row.get("thumb") or row.get("cover_image") or "").strip(),
        "genres": genres,
        "resource_url": str(row.get("resource_url") or "").strip(),
        "uri": (
            f"https://www.discogs.com{row['uri']}"
            if str(row.get("uri") or "").startswith("/")
            else str(row.get("uri") or "")
        ),
    }


def suggest_discogs_releases(
    query: str,
    *,
    client: httpx.Client | None = None,
    db: Session | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """AJAX autocomplete: catalog / free-text → release suggestions (no full fetch)."""
    q = re.sub(r"\s+", " ", (query or "").strip())
    if len(q) < 2:
        return []
    limit = max(1, min(int(limit or 10), 25))

    if db is not None:
        try:
            if not load_discogs_config(db).get("enabled", True):
                raise DiscogsError(
                    "Discogs connector disabled in OPS — enable under Discogs tab",
                    status_code=503,
                )
        except DiscogsError:
            raise
        except Exception:  # noqa: BLE001
            pass

    own = client is None
    http = client or httpx.Client(timeout=15.0, headers={"User-Agent": _UA}, follow_redirects=True)
    auth = _auth_params(db)
    try:
        raw_hits: list[dict[str, Any]] = []
        # Catalog-number first when the query looks like a label/catno.
        looks_catno = bool(re.search(r"\d", q)) and (
            bool(re.search(r"[-–—./\s]", q)) or len(re.sub(r"\D", "", q)) >= 4
        )
        if looks_catno:
            for variant in _catno_variants(q)[:4]:
                data = _get_json(
                    http,
                    f"{_API}/database/search",
                    params={**auth, "type": "release", "catno": variant, "per_page": str(limit)},
                )
                for row in (data or {}).get("results") or []:
                    if isinstance(row, dict):
                        raw_hits.append(row)
                if raw_hits:
                    break

        data = _get_json(
            http,
            f"{_API}/database/search",
            params={**auth, "type": "release", "q": q, "per_page": str(limit)},
        )
        for row in (data or {}).get("results") or []:
            if isinstance(row, dict):
                raw_hits.append(row)

        seen: set[int] = set()
        classical: list[dict[str, Any]] = []
        other: list[dict[str, Any]] = []
        for row in raw_hits:
            hit = _normalize_search_hit(row)
            if hit is None or hit["id"] in seen:
                continue
            seen.add(hit["id"])
            if "Classical" in (hit.get("genres") or []):
                classical.append(hit)
            else:
                other.append(hit)
        out = classical + other
        return out[:limit]
    except DiscogsError:
        raise
    except httpx.HTTPError as exc:
        logger.warning("discogs_suggest_failed q=%s err=%s", q, exc)
        raise DiscogsError("Discogs unavailable", status_code=502) from exc
    finally:
        if own:
            http.close()


def _parse_release_core(payload: dict[str, Any]) -> dict[str, Any]:
    """Single credit/id/URI parse for analyze_* and build_diary_snapshot (META-001 §3.5)."""
    raw = dict(payload.get("raw") or {})
    kind = str(payload.get("kind") or "release")
    release_id = int(payload.get("main_release_id") or raw.get("id") or payload.get("id") or 0)
    master_id = int(payload.get("id") or 0) if kind == "master" else None
    if kind == "release":
        master_id = None
        if isinstance(raw.get("master_id"), int):
            master_id = int(raw["master_id"])

    artists = _names(list(raw.get("artists") or []))
    extras = list(raw.get("extraartists") or [])
    composers = _role_names(extras, _COMPOSER_ROLE)
    composer_names = {c.lower() for c in composers}
    ensembles = _role_names(extras, _ENSEMBLE_ROLE)
    ensemble_names = {e.lower() for e in ensembles}
    for name in artists:
        low = name.lower()
        if _ENSEMBLE_ROLE.search(name) and low not in ensemble_names:
            ensembles.append(name)
            ensemble_names.add(low)

    role_performers = _role_names(extras, _PERFORMER_ROLE)
    performer_sources = role_performers or artists
    performers: list[str] = []
    for name in performer_sources:
        low = name.lower()
        if low in composer_names or low in ensemble_names:
            continue
        if name not in performers:
            performers.append(name)

    labels: list[dict[str, str]] = []
    catno = ""
    label_name = ""
    for lab in raw.get("labels") or []:
        if not isinstance(lab, dict):
            continue
        entry = {"name": str(lab.get("name") or ""), "catno": str(lab.get("catno") or "")}
        labels.append(entry)
        if not label_name and entry["name"]:
            label_name = entry["name"]
        if not catno and entry["catno"]:
            catno = entry["catno"]

    uri = str(raw.get("uri") or "")
    if uri and not uri.startswith("http"):
        uri = f"https://www.discogs.com{uri}"
    if not uri and release_id:
        uri = f"https://www.discogs.com/release/{release_id}"

    cover, thumb = _cover_urls(raw)
    return {
        "raw": raw,
        "kind": kind,
        "release_id": release_id,
        "master_id": master_id,
        "artists": artists,
        "composers": composers,
        "performers": performers,
        "ensembles": ensembles,
        "year": raw.get("year") or "",
        "labels": labels,
        "label_name": label_name,
        "catno": catno,
        "uri": uri,
        "cover": cover,
        "thumb": thumb,
        "title": str(raw.get("title") or "").strip(),
        "genres": [str(g) for g in (raw.get("genres") or []) if g][:8],
        "styles": [str(s) for s in (raw.get("styles") or []) if s][:8],
        "country": str(raw.get("country") or "").strip(),
    }


def _build_release_structure_safe(core: dict[str, Any]) -> dict[str, Any]:
    """SPEC-034 / META-001 §4.1 — structure map before listening deepen."""
    try:
        import sys
        from pathlib import Path

        skills = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if skills.is_dir() and str(skills) not in sys.path:
            sys.path.insert(0, str(skills))
        from aulos_skills.release_structure import (
            assert_structure_ready,
            build_release_structure,
            expansion_plan,
        )

        st = build_release_structure(
            core["raw"],
            release_id=core.get("release_id"),
            master_id=core.get("master_id"),
            uri=str(core.get("uri") or ""),
            composers=list(core.get("composers") or []),
            performers=list(core.get("performers") or []),
            ensembles=list(core.get("ensembles") or []),
        )
        d = st.to_dict()
        d["expansion_plan"] = expansion_plan(st)
        d["structure_hard_fails"] = assert_structure_ready(st)
        return d
    except Exception as exc:  # noqa: BLE001
        logger.warning("release_structure_build_failed err=%s", exc)
        return {
            "schema": "aulos.release_structure/v1",
            "structure_ready": False,
            "gaps": ["structure_builder_error"],
            "structure_hard_fails": ["release_structure_not_ready", "structure_gap:structure_builder_error"],
            "program": [],
            "shape": "unknown",
        }


def analyze_discogs_release(payload: dict[str, Any]) -> dict[str, Any]:
    """Turn Discogs JSON into listening-intent fields + dossier seeds."""
    core = _parse_release_core(payload)
    raw = core["raw"]
    kind = core["kind"]
    release_id = core["release_id"]
    master_id = core["master_id"]
    artists = core["artists"]
    composers = core["composers"]
    performers = core["performers"]
    ensembles = core["ensembles"]
    year = core["year"]
    labels = core["labels"]
    uri = core["uri"]

    release_structure = _build_release_structure_safe(core)
    if not composers and release_structure.get("composers"):
        composers = [str(c) for c in (release_structure.get("composers") or []) if c]
    work_title = _guess_work_title(raw, artists)
    composer = " / ".join(composers[:8]) if len(composers) > 1 else (composers[0] if composers else "")

    label_note = ""
    if labels:
        lab0 = labels[0]
        bits = [lab0.get("name") or "", lab0.get("catno") or "", str(year or "")]
        label_note = " · ".join(b for b in bits if b)

    performer_line = ", ".join(performers[:6])
    ensemble_line = ", ".join(ensembles[:4])
    catno_note = ""
    if payload.get("catno_query"):
        catno_note = f", catno {payload.get('catno_match') or payload.get('catno_query')}"
    # Avoid "I'm listening to Composer — …" shapes that confuse intake dash-parsing
    # into composer="to Wolfgang…" and titles that swallow "performed by …".
    title_bit = f"{composer} — {work_title}" if composer else work_title
    intent = (
        f"Listening guide for {title_bit}. "
        f"{f'Performers: {performer_line}. ' if performer_line else ''}"
        f"{f'Ensembles: {ensemble_line}. ' if ensemble_line else ''}"
        f"Discogs release {release_id}{catno_note}"
        f"{f', {year}' if year else ''}. "
        "Write a professional listening guide for this work, "
        "highlighting this recording's performers and sound."
    ).strip()

    seed = {
        "work_title": work_title,
        "composer": composer,
        "interpretations": [
            {
                "artist": performer_line or ensemble_line or (artists[0] if artists else "Unknown"),
                "year": str(year or ""),
                "instrument": "",
                "era_note": "Discogs release seed",
                "why_listen": "Primary pressing named by the listener via /discogs.",
                "discogs_url": uri,
            }
        ],
        "vinyl_and_discography": [
            {
                "label": label_note or (labels[0]["name"] if labels else "Discogs"),
                "url": uri,
                "note": f"Source release #{release_id}"
                + (f" · master #{master_id}" if master_id else "")
                + (f" · catno {payload.get('catno_query')}" if payload.get("catno_query") else ""),
            }
        ],
        "_provenance": {
            "source": "discogs",
            "discogs": {
                "kind": kind,
                "release_id": release_id,
                "master_id": master_id,
                "uri": uri,
                "catno_query": payload.get("catno_query"),
                "catno_match": payload.get("catno_match"),
                "resolved_from": payload.get("resolved_from") or "release_id",
                "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "genres": list(raw.get("genres") or []),
                "styles": list(raw.get("styles") or []),
            },
            "release_structure": {
                "shape": release_structure.get("shape"),
                "structure_ready": release_structure.get("structure_ready"),
                "program_count": len(release_structure.get("program") or []),
                "catalog_numbers_all": list(
                    release_structure.get("catalog_numbers_all") or []
                )[:24],
            },
        },
        "release_structure": release_structure,
    }

    search_q = quote(" ".join(p for p in [composer, work_title] if p))
    if not uri:
        seed["vinyl_and_discography"][0]["url"] = f"https://www.discogs.com/search/?q={search_q}"

    program_bits = []
    for p in (release_structure.get("program") or [])[:8]:
        if not isinstance(p, dict):
            continue
        cats = ", ".join(p.get("catalog_numbers") or [])
        program_bits.append(f"{p.get('title')}" + (f" [{cats}]" if cats else ""))

    return {
        "release_id": release_id,
        "master_id": master_id,
        "kind": kind,
        "work_title": work_title,
        "composer": composer,
        "composers": composers,
        "performers": performers,
        "ensembles": ensembles,
        "artists": artists,
        "year": year,
        "labels": labels,
        "uri": uri,
        "catno_query": payload.get("catno_query"),
        "track_titles": [
            str(t.get("title") or "").strip()
            for t in (raw.get("tracklist") or [])
            if isinstance(t, dict) and str(t.get("title") or "").strip()
        ][:24],
        "release_structure": release_structure,
        "listening_intent": intent,
        "work_hint": (
            f"{composer} — {work_title}".strip(" —") if composer else work_title
        ),
        "kb_seed": seed,
        "rag_snippets": [
            f"Discogs {kind} #{release_id}: {raw.get('title')}",
            f"Composer credits: {', '.join(composers) or 'unlisted'}",
            f"Performers: {performer_line or 'unlisted'}",
            f"Ensembles: {ensemble_line or 'unlisted'}",
            f"Label: {label_note or 'n/a'}",
            f"URL: {uri}",
            (
                f"Release structure: {release_structure.get('shape')} "
                f"ready={release_structure.get('structure_ready')} "
                f"program={len(release_structure.get('program') or [])}"
            ),
            *(f"Program work: {bit}" for bit in program_bits),
        ],
    }


def _guess_source_kind(raw: dict[str, Any]) -> str:
    formats = raw.get("formats") or []
    names: list[str] = []
    for fmt in formats:
        if isinstance(fmt, dict):
            names.append(str(fmt.get("name") or "").lower())
            for d in fmt.get("descriptions") or []:
                names.append(str(d).lower())
    blob = " ".join(names)
    if "vinyl" in blob or "lp" in blob:
        return "vinyl"
    if "cd" in blob or "compact disc" in blob:
        return "cd"
    return "release"


def _cover_urls(raw: dict[str, Any]) -> tuple[str, str]:
    cover = ""
    thumb = str(raw.get("thumb") or "").strip()
    images = raw.get("images") or []
    if isinstance(images, list):
        for img in images:
            if not isinstance(img, dict):
                continue
            uri = str(img.get("uri") or img.get("resource_url") or "").strip()
            if not uri:
                continue
            itype = str(img.get("type") or "").lower()
            if itype == "primary" or not cover:
                cover = uri
            if itype == "primary":
                break
    if not cover:
        cover = thumb
    if not thumb:
        thumb = cover
    return cover, thumb


def build_diary_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize Discogs release payload into ListeningDiary ReleaseSnapshot (SPEC-019)."""
    core = _parse_release_core(payload)
    raw = core["raw"]
    tracklist: list[dict[str, Any]] = []
    for t in raw.get("tracklist") or []:
        if not isinstance(t, dict):
            continue
        title = str(t.get("title") or "").strip()
        if not title:
            continue
        tracklist.append(
            {
                "position": str(t.get("position") or "").strip(),
                "title": title,
                "duration": str(t.get("duration") or "").strip(),
                "type": str(t.get("type_") or "track").strip() or "track",
            }
        )

    source_kind = _guess_source_kind(raw)
    fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    release_id = core["release_id"]
    uri = core["uri"]
    release_structure = _build_release_structure_safe(core)
    composers = core["composers"] or [
        str(c) for c in (release_structure.get("composers") or []) if c
    ]
    return {
        "provider": "discogs",
        "external_id": str(release_id),
        "source_kind": source_kind,
        "title": core["title"],
        "cover_image_url": core["cover"],
        "thumb_url": core["thumb"],
        "composers": composers,
        "performers": core["performers"],
        "ensembles": core["ensembles"],
        "artists": core["artists"],
        "year": str(core["year"] or ""),
        "label": core["label_name"],
        "catno": core["catno"],
        "labels": core["labels"],
        "country": core["country"],
        "uri": uri,
        "tracklist": tracklist,
        "genres": core["genres"],
        "styles": core["styles"],
        "release_structure": release_structure,
        "fetched_at": fetched_at,
        "provenance": {
            "kind": core["kind"],
            "release_id": release_id,
            "master_id": core["master_id"],
            "uri": uri,
            "fetched_at": fetched_at,
            "structure_ready": release_structure.get("structure_ready"),
            "structure_shape": release_structure.get("shape"),
        },
    }


def suggest_discogs_artists(
    q: str,
    *,
    client: httpx.Client | None = None,
    db: Session | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search Discogs artists by name; returns lightweight hits."""
    query = (q or "").strip()
    if len(query) < 1:
        return []
    own = client is None
    http = client or httpx.Client(timeout=20.0, headers={"User-Agent": _UA}, follow_redirects=True)
    params = {**_auth_params(db), "q": query, "type": "artist", "per_page": str(min(limit, 10))}
    try:
        data = _get_json(http, f"{_API}/database/search", params=params) or {}
        results = data.get("results") or []
        out: list[dict[str, Any]] = []
        for row in results:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title") or "").strip()
            rid = row.get("id")
            if not title or rid is None:
                continue
            out.append(
                {
                    "id": int(rid),
                    "title": title,
                    "thumb": str(row.get("thumb") or ""),
                    "resource_url": str(row.get("resource_url") or ""),
                    "uri": str(row.get("uri") or ""),
                }
            )
            if len(out) >= limit:
                break
        return out
    except DiscogsError:
        raise
    except httpx.HTTPError as exc:
        logger.warning("discogs_artist_search_failed q=%s err=%s", query, exc)
        raise DiscogsError("Discogs unavailable", status_code=502) from exc
    finally:
        if own:
            http.close()


def _artist_name_score(query: str, title: str) -> float:
    q = re.sub(r"\s+", " ", (query or "").strip().lower())
    t = re.sub(r"\s+", " ", (title or "").strip().lower())
    # Discogs titles sometimes "Name (n)"
    t = re.sub(r"\s*\(\d+\)\s*$", "", t).strip()
    if not q or not t:
        return 0.0
    if q == t:
        return 1.0
    if q in t or t in q:
        return 0.85
    qt = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", q))
    tt = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", t))
    if not qt or not tt:
        return 0.0
    return len(qt & tt) / max(len(qt), len(tt))


def _strip_discogs_disambig(name: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", (name or "").strip()).strip()


def resolve_discogs_artist_card(
    name: str,
    *,
    kind: str = "person",
    client: httpx.Client | None = None,
    db: Session | None = None,
) -> dict[str, Any] | None:
    """Fetch Discogs artist profile as person-card fields (first authority for 聆乐 names)."""
    query = (name or "").strip()
    if not query:
        return None
    if db is not None:
        try:
            if not load_discogs_config(db).get("enabled", True):
                return None
        except Exception:  # noqa: BLE001
            pass
    if not _auth_params(db):
        logger.info("discogs_artist_skip_no_auth name=%s", query)
        return None

    own = client is None
    http = client or httpx.Client(timeout=20.0, headers={"User-Agent": _UA}, follow_redirects=True)
    try:
        hits = suggest_discogs_artists(query, client=http, db=db, limit=8)
        if not hits:
            return None
        # Prefer exact/high score; among ties prefer titles without "(2)" disambiguation
        def rank_key(h: dict[str, Any]) -> tuple[float, int, str]:
            title = str(h.get("title") or "")
            score = _artist_name_score(query, title)
            disambig_penalty = 1 if re.search(r"\(\d+\)\s*$", title) else 0
            return (score, -disambig_penalty, title)

        ranked = sorted(hits, key=rank_key, reverse=True)
        best = ranked[0]
        score = _artist_name_score(query, str(best.get("title") or ""))
        # Prefer near-exact artist title; weak fuzzy matches invent wrong people
        if score < 0.72:
            return None
        artist_id = int(best["id"])
        params = _auth_params(db)
        raw = _get_json(http, f"{_API}/artists/{artist_id}", params=params)
        if not raw:
            return None
        display = _strip_discogs_disambig(str(raw.get("name") or best.get("title") or query))
        if _artist_name_score(query, display) < 0.72:
            return None
        profile = str(raw.get("profile") or "").strip()
        profile = re.sub(r"\[/?[^\]]+\]", "", profile)
        profile = re.sub(r"\s+\n", "\n", profile).strip()
        # Reject placeholder / truncated Discogs stubs
        if profile and (
            len(profile) < 40
            or profile.lower().startswith("please note")
            or profile.endswith(" is .")
            or profile.endswith(" is.")
        ):
            profile = ""
        if len(profile) > 1200:
            profile = profile[:1197].rstrip() + "…"
        if not profile and not display:
            return None
        images = raw.get("images") or []
        portrait = ""
        if isinstance(images, list):
            for img in images:
                if isinstance(img, dict) and img.get("uri"):
                    portrait = str(img.get("uri") or "")
                    if str(img.get("type") or "") == "primary":
                        break
        uri = str(raw.get("uri") or best.get("uri") or "")
        if uri and not uri.startswith("http"):
            uri = f"https://www.discogs.com{uri}"
        realname = str(raw.get("realname") or "").strip()
        namevars = [str(x) for x in (raw.get("namevariations") or []) if x][:12]
        return {
            "name": query,
            "kind": kind,
            "display_name": display,
            "summary": profile or (f"{display}" + (f" — also known as {realname}" if realname else "")),
            "lifespan": "",
            "era": "",
            "portrait_url": portrait,
            "external_ids": {
                "discogs": str(artist_id),
                "discogs_uri": uri,
                "person_kind": kind,
                "realname": realname,
                "namevariations": namevars,
            },
            "provenance": [{"source_id": "discogs", "url": uri or f"https://www.discogs.com/artist/{artist_id}"}],
            "source": "enriched",
            "authority": "discogs",
        }
    except DiscogsError as exc:
        logger.warning("discogs_artist_resolve_failed name=%s err=%s", query, exc)
        return None
    except httpx.HTTPError as exc:
        logger.warning("discogs_artist_http_failed name=%s err=%s", query, exc)
        return None
    finally:
        if own:
            http.close()


def resolve_discogs_message(
    message: str,
    *,
    client: httpx.Client | None = None,
    db: Session | None = None,
) -> dict[str, Any] | None:
    """If message is a /discogs command, fetch+analyze; else None."""
    try:
        from aulos_skills.intake_parse import parse_discogs_command
    except ImportError:
        parse_discogs_command = None  # type: ignore[assignment]
    if parse_discogs_command is None:
        return None
    cmd = parse_discogs_command(message)
    if not cmd:
        return None
    if cmd.get("catno"):
        payload = search_discogs_by_catno(cmd["catno"], client=client, db=db)
    else:
        payload = fetch_discogs_entity(cmd["release_id"], client=client, db=db)
    analysis = analyze_discogs_release(payload)
    analysis["command"] = cmd
    return analysis


# Back-compat alias
resolve_discog_message = resolve_discogs_message
