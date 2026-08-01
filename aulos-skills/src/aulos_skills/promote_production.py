"""Generic promote staged craft → Catalog stubs + production craft (SPEC-031).

Case-agnostic: any staged promote_candidate graduates through the same pipeline.
No per-work or per-composer Python branches.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.craft_packs import craft_packs_root, load_craft_pack
from aulos_skills.identity import default_catalog_root, load_catalog
from aulos_skills.promote_staging import load_staging_craft, validate_work_id
from aulos_skills.salon_codex import coerce_dict

_TOKEN_RE = re.compile(r"[a-z0-9\u4e00-\u9fff]{2,}", re.I)


def _slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def composer_id_from_name(name: str) -> str:
    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]
    if not parts:
        return "unknown-composer"
    # full-name slug when multi-token; else single token
    if len(parts) >= 2:
        return _slug(" ".join(parts)) or "unknown-composer"
    return _slug(parts[0]) or "unknown-composer"


def _tokens(*parts: str) -> list[str]:
    seen: list[str] = []
    for part in parts:
        for t in _TOKEN_RE.findall(part or ""):
            tl = t.lower()
            if tl not in seen and len(tl) >= 2:
                seen.append(tl)
    return seen[:16]


def _safe_under(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    root_r = root.resolve()
    if root_r not in resolved.parents and resolved.parent != root_r:
        raise ValueError(f"path escaped root: {path}")
    return resolved


def _load_index(catalog_root: Path) -> dict[str, Any]:
    path = catalog_root / "index.yaml"
    if not path.is_file():
        return {"composers": [], "works": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {"composers": [], "works": []}


def _write_index(catalog_root: Path, index: dict[str, Any]) -> None:
    path = catalog_root / "index.yaml"
    path.write_text(
        yaml.safe_dump(index, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _ensure_index_entry(
    entries: list[Any], *, entry_id: str, rel_path: str
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    found = False
    for raw in entries or []:
        if not isinstance(raw, dict):
            continue
        item = {"id": str(raw.get("id") or ""), "path": str(raw.get("path") or "")}
        if item["id"] == entry_id:
            item["path"] = rel_path
            found = True
        if item["id"]:
            out.append(item)
    if not found:
        out.append({"id": entry_id, "path": rel_path})
    return out


def materialize_composer_stub(
    *,
    composer_name: str,
    era: str = "",
) -> dict[str, Any]:
    name = (composer_name or "").strip() or "Unknown Composer"
    cid = composer_id_from_name(name)
    aliases = _tokens(name)
    # keep short last-name alias when multi-token
    parts = [p for p in re.split(r"\s+", name) if p]
    if parts:
        last = _slug(parts[-1])
        if last and last not in aliases:
            aliases.insert(0, last)
    return {
        "composer_id": cid,
        "name_en": name,
        "name_zh": "",
        "aliases": aliases[:8],
        "lifespan": "",
        "era": (era or "").strip(),
        "provenance": {
            "authority": "promote-production pipeline (SPEC-031)",
            "notes": "Composer stub from unknown-case promote — thicken via knowledge plane.",
        },
    }


def materialize_work_stub(
    *,
    work_id: str,
    composer_id: str,
    work_title: str,
    family_id: str,
    facets: dict[str, Any],
) -> dict[str, Any]:
    title = (work_title or "").strip()
    fac_inst = [str(x) for x in (facets.get("instruments") or []) if x]
    fac_forms = [str(x) for x in (facets.get("forms") or []) if x]
    era = str(facets.get("era") or "")
    distinctive = _tokens(title, " ".join(fac_forms), " ".join(fac_inst))
    return {
        "work_id": work_id,
        "composer_id": composer_id,
        "canonical_title": title,
        "canonical_title_zh": "",
        "aliases": distinctive[:8],
        "catalog_numbers": [],
        "facets": {
            "instruments": fac_inst,
            "forms": fac_forms,
            "era": era,
        },
        "family_id": family_id or "chamber-generic",
        "corpus_key": None,
        "ambient_ref": None,
        "identity": {
            "distinctive_tokens": distinctive[:12],
            "conflict_work_ids": [],
            "conflict_markers": [],
        },
        "provenance": {
            "authority": "promote-production pipeline (SPEC-031)",
            "notes": "Work stub from dimensional unknown-case promote — not a hand case patch.",
        },
    }


def _production_craft_from_staging(staging: dict[str, Any]) -> dict[str, Any]:
    out = dict(staging or {})
    caveats = [
        c
        for c in list(out.get("myths_and_caveats") or [])
        if "Staged from unknown-case" not in str(c)
    ]
    caveats.append(
        "Promoted via SPEC-031 pipeline — verify anecdotes before stating as fact."
    )
    out["myths_and_caveats"] = caveats
    prov = coerce_dict(out.get("_provenance"))
    prov["promote_staged"] = False
    prov["promote_production"] = True
    prov["promoted_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out["_provenance"] = prov
    return out


def promote_staged_to_production(
    *,
    candidate: dict[str, Any],
    composer: str = "",
    work_title: str = "",
    staging_pack: dict[str, Any] | None = None,
    catalog_root: Path | None = None,
    craft_root: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Graduate any staged promote_candidate into Catalog + production craft."""
    cand = dict(candidate or {})
    wid = str(cand.get("suggested_work_id") or "").strip()
    if not validate_work_id(wid):
        raise ValueError(f"invalid suggested_work_id: {wid!r}")

    cat_root = Path(catalog_root) if catalog_root else default_catalog_root()
    cr_root = Path(craft_root) if craft_root else craft_packs_root()
    (cat_root / "composers").mkdir(parents=True, exist_ok=True)
    (cat_root / "works").mkdir(parents=True, exist_ok=True)
    cr_root.mkdir(parents=True, exist_ok=True)

    staging = dict(staging_pack or {}) or load_staging_craft(wid)
    if not staging:
        raise ValueError(f"no staging craft for {wid}")

    name = (composer or str(staging.get("composer") or "")).strip()
    title = (work_title or str(staging.get("work_title") or "")).strip()
    if not name or not title:
        raise ValueError("composer and work_title required for promote-to-production")

    facets = coerce_dict(cand.get("facets"))
    if not facets.get("instruments") and not facets.get("forms"):
        fac_prov = coerce_dict(coerce_dict(staging.get("_provenance")).get("facets"))
        facets = fac_prov or facets
    family_id = str(cand.get("family_id") or staging.get("family_id") or "chamber-generic")
    era = str(facets.get("era") or staging.get("era") or "")

    composer_stub = materialize_composer_stub(composer_name=name, era=era)
    cid = str(composer_stub["composer_id"])
    composer_path = cat_root / "composers" / f"{cid}.yaml"
    _safe_under(cat_root / "composers", composer_path)
    if composer_path.is_file() and not overwrite:
        # Keep existing composer card; still ensure index entry
        existing = yaml.safe_load(composer_path.read_text(encoding="utf-8")) or {}
        if isinstance(existing, dict) and existing.get("composer_id"):
            cid = str(existing["composer_id"])
            composer_stub = existing
    else:
        composer_path.write_text(
            yaml.safe_dump(composer_stub, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    work_stub = materialize_work_stub(
        work_id=wid,
        composer_id=cid,
        work_title=title,
        family_id=family_id,
        facets=facets,
    )
    work_path = cat_root / "works" / f"{wid}.yaml"
    _safe_under(cat_root / "works", work_path)
    if work_path.is_file() and not overwrite:
        raise FileExistsError(f"production Catalog work already exists: {wid}")
    work_path.write_text(
        yaml.safe_dump(work_stub, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    index = _load_index(cat_root)
    index["composers"] = _ensure_index_entry(
        list(index.get("composers") or []),
        entry_id=cid,
        rel_path=f"composers/{cid}.yaml",
    )
    index["works"] = _ensure_index_entry(
        list(index.get("works") or []),
        entry_id=wid,
        rel_path=f"works/{wid}.yaml",
    )
    _write_index(cat_root, index)

    craft = _production_craft_from_staging(staging)
    craft["work_id"] = wid
    craft_path = cr_root / f"{wid}.yaml"
    _safe_under(cr_root, craft_path)
    if craft_path.is_file() and not overwrite:
        raise FileExistsError(f"production craft already exists: {wid}")
    craft_path.write_text(
        yaml.safe_dump(craft, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # Invalidate caches so subsequent resolve/synthesize see new records
    try:
        load_catalog.cache_clear()
    except Exception:  # noqa: BLE001
        pass
    try:
        load_craft_pack.cache_clear()
    except Exception:  # noqa: BLE001
        pass

    return {
        "ok": True,
        "work_id": wid,
        "composer_id": cid,
        "catalog_work_path": str(work_path),
        "catalog_composer_path": str(composer_path),
        "craft_path": str(craft_path),
        "family_id": family_id,
        "promoted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
