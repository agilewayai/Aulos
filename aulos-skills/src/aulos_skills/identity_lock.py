"""Authoritative identity lock — class gate against sibling-work drift.

Root failure mode (guide #47 class): when Catalog miss / weak lock, LLM or KB
substitutes another famous work by the same composer/performer (concerto → Requiem).

This module is **data + token driven** (SPEC-008): no per-work Python branches.
Catalog YAML still improves recall; form-lock policy + catalog-number lock work
even when the specific pressing is not yet a Catalog work record.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Köchel / BWV / Op. / Hob. / D. style catalog numbers.
# SPEC-033: allow chained siblings after one prefix (BWV 1041 • 1042 / K. 330 / 331).
_CATALOG_NUM_RE = re.compile(
    r"(?i)\b("
    r"(?:bwv|op\.?|opus|k\.?v?\.?|kv\.?|hob\.?|d\.?|wwv|rv)\s*"
    r"\d{1,4}[a-z]?"
    r"(?:"
    r"\s*[-–—/&]\s*\d{1,4}[a-z]?"
    r"|"
    r"(?:\s*(?:[•·/,;&]|and|und)\s*\d{1,4}[a-z]?)+"
    r")?"
    r")\b"
)
_CATALOG_CHAIN_RE = re.compile(
    r"(?i)\b(?P<prefix>bwv|op\.?|opus|k\.?v?\.?|kv\.?|hob\.?|d\.?|wwv|rv)\s*"
    r"(?P<body>\d{1,4}[a-z]?(?:\s*(?:[-–—/&•·,;]|and|und)\s*\d{1,4}[a-z]?)*)"
)

_CORE_DOSSIER_KEYS = (
    "work_title",
    "listening_thesis",
    "work_introduction",
    "form",
    "era",
    "catalog",
)

# Narrative chambers — work_title is often force-copied from the lock and must
# not alone count as "form preserved" when thesis/form drifted to a sibling work.
_NARRATIVE_KEYS = (
    "listening_thesis",
    "work_introduction",
    "form",
    "era",
    "catalog",
)


def default_form_lock_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "aulos-listening-corpus"
        / "assets"
        / "catalog"
        / "policies"
        / "form_lock_groups.yaml"
    )


def normalize_catalog_number(raw: str) -> str:
    s = (raw or "").lower().strip()
    s = s.replace("kv.", "k.").replace("kv ", "k ")
    s = re.sub(r"\s+", "", s)
    s = s.replace("opus", "op").replace("op.", "op")
    s = re.sub(r"^k\.?", "k", s)
    s = re.sub(r"^op\.?", "op", s)
    s = re.sub(r"^bwv\.?", "bwv", s)
    return s


def extract_catalog_numbers(text: str) -> set[str]:
    found: set[str] = set()
    for m in _CATALOG_CHAIN_RE.finditer(text or ""):
        prefix = m.group("prefix") or ""
        body = m.group("body") or ""
        nums = re.findall(r"\d{1,4}[a-z]?", body, flags=re.I)
        if not nums:
            continue
        for num in nums:
            n = normalize_catalog_number(f"{prefix} {num}")
            if n:
                found.add(n)
    # Fallback for odd single matches the chain regex missed
    if not found:
        for m in _CATALOG_NUM_RE.finditer(text or ""):
            n = normalize_catalog_number(m.group(1))
            if n:
                found.add(n)
    return found


@lru_cache(maxsize=4)
def load_form_lock_policy(path_str: str | None = None) -> dict[str, Any]:
    path = Path(path_str) if path_str else default_form_lock_path()
    if not path.is_file():
        return {"families": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    families = data.get("families") or {}
    return {"families": dict(families)}


@dataclass
class IdentityLock:
    """Authoritative lock derived from Discogs / diary / intake title+message."""

    work_title: str = ""
    catalog_numbers: set[str] = field(default_factory=set)
    form_families: set[str] = field(default_factory=set)
    alien_markers: list[str] = field(default_factory=list)

    @property
    def strong(self) -> bool:
        return bool(self.catalog_numbers or self.form_families)


def _family_anchor_hit(blob: str, anchors: list[Any]) -> bool:
    low = blob.lower()
    for a in anchors or []:
        tok = str(a).lower().strip()
        if len(tok) >= 2 and tok in low:
            return True
    return False


def build_identity_lock(
    *,
    work_title: str = "",
    work_hint: str = "",
    raw_message: str = "",
    policy: dict[str, Any] | None = None,
) -> IdentityLock:
    blob = " ".join(x for x in (work_title, work_hint, raw_message) if x)
    numbers = extract_catalog_numbers(blob)
    pol = policy or load_form_lock_policy()
    families = dict(pol.get("families") or {})
    hit_ids: set[str] = set()
    aliens: list[str] = []
    seen: set[str] = set()
    blob_l = blob.lower()
    for fid, spec in families.items():
        if not isinstance(spec, dict):
            continue
        if _family_anchor_hit(blob, list(spec.get("anchors") or [])):
            hit_ids.add(str(fid))
            for m in spec.get("alien_markers") or []:
                ml = str(m).lower().strip()
                if not ml or ml in seen or ml in blob_l:
                    continue
                seen.add(ml)
                aliens.append(ml)
    # More specific chamber/duo families suppress solo_keyboard (SPEC-032):
    # bare keyboard anchors must not add cello/orchestra aliens onto duo shelves.
    if "duo_cello_piano" in hit_ids and "solo_keyboard" in hit_ids:
        hit_ids.discard("solo_keyboard")
        # Rebuild aliens without the suppressed family.
        aliens = []
        seen = set()
        for fid in hit_ids:
            spec = families.get(fid) or {}
            if not isinstance(spec, dict):
                continue
            for m in spec.get("alien_markers") or []:
                ml = str(m).lower().strip()
                if not ml or ml in seen or ml in blob_l:
                    continue
                seen.add(ml)
                aliens.append(ml)

    return IdentityLock(
        work_title=work_title or "",
        catalog_numbers=numbers,
        form_families=hit_ids,
        alien_markers=aliens,
    )


def identity_lock_alien_markers(
    *,
    work_title: str = "",
    work_hint: str = "",
    raw_message: str = "",
) -> list[str]:
    return list(
        build_identity_lock(
            work_title=work_title, work_hint=work_hint, raw_message=raw_message
        ).alien_markers
    )


def _core_dossier_blob(dossier: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in _CORE_DOSSIER_KEYS:
        val = dossier.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    for zkey in ("zh", "zh_hans", "zh_hant"):
        zh = dossier.get(zkey)
        if isinstance(zh, dict):
            for key in _CORE_DOSSIER_KEYS:
                val = zh.get(key)
                if isinstance(val, str) and val.strip():
                    parts.append(val)
    return "\n".join(parts)


def _narrative_dossier_blob(dossier: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in _NARRATIVE_KEYS:
        val = dossier.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    for zkey in ("zh", "zh_hans", "zh_hant"):
        zh = dossier.get(zkey)
        if isinstance(zh, dict):
            for key in _NARRATIVE_KEYS:
                val = zh.get(key)
                if isinstance(val, str) and val.strip():
                    parts.append(val)
    return "\n".join(parts)


def _pollution_scan_blob(dossier: dict[str, Any]) -> str:
    """Chambers where foreign-work rhetoric must not hide behind a force-copied title.

    Excludes related_works / interpretations (peer citations are legal there).
    """
    parts = [_narrative_dossier_blob(dossier)]
    for key in ("width_points", "depth_points", "myths_and_caveats", "practice_notes"):
        val = dossier.get(key)
        if isinstance(val, list):
            parts.extend(str(x) for x in val if x)
        elif isinstance(val, str) and val.strip():
            parts.append(val)
    for zkey in ("zh", "zh_hans", "zh_hant"):
        zh = dossier.get(zkey)
        if not isinstance(zh, dict):
            continue
        for key in ("width_points", "depth_points", "myths_and_caveats", "practice_notes"):
            val = zh.get(key)
            if isinstance(val, list):
                parts.extend(str(x) for x in val if x)
            elif isinstance(val, str) and val.strip():
                parts.append(val)
    return "\n".join(parts)


def dossier_betrays_identity_lock(
    dossier: dict[str, Any] | None,
    *,
    work_title: str = "",
    work_hint: str = "",
    raw_message: str = "",
) -> bool:
    """True when dossier swapped the locked work for a sibling famous piece.

    Class rules (all composers/works):
    1. Lock has catalog numbers; craft narrative has *other* catalog numbers →
       betrayal even when a lock number was force-copied onto work_title/thesis
       (regen/self-poison mask class).
    2. Lock has a form family; narrative hits opposing alien markers and
       does not preserve lock form/numbers in narrative → betrayal.
    """
    if not dossier:
        return False
    lock = build_identity_lock(work_title=work_title, work_hint=work_hint, raw_message=raw_message)
    if not lock.strong:
        return False

    narrative = _narrative_dossier_blob(dossier)
    scan = _pollution_scan_blob(dossier)
    if not scan.strip():
        return False
    narrative_l = narrative.lower()
    scan_l = scan.lower()

    lock_nums = set(lock.catalog_numbers)
    scan_nums = extract_catalog_numbers(scan)

    # Rule 1: any competing catalog number in craft chambers is betrayal.
    # Force-copied lock numbers must not mask foreign Op./BWV/K. pollution.
    if lock_nums:
        foreign = scan_nums - lock_nums
        if foreign:
            return True

    # Rule 2: opposing form-family aliens dominate thesis/form (ignore force-copied work_title)
    if not lock.alien_markers:
        return False
    alien_hits = [m for m in lock.alien_markers if m in scan_l or m in narrative_l]
    if not alien_hits:
        return False

    form_preserved = False
    pol = load_form_lock_policy()
    for fid in lock.form_families:
        spec = (pol.get("families") or {}).get(fid) or {}
        if _family_anchor_hit(narrative, list(spec.get("anchors") or [])):
            form_preserved = True
            break
    narrative_nums = extract_catalog_numbers(narrative)
    num_preserved = bool(lock_nums & narrative_nums)
    if not form_preserved and not num_preserved:
        return True
    if lock_nums and not num_preserved and any(len(m) >= 4 for m in alien_hits):
        return True
    return False


def identity_shell_dossier(
    *,
    work_title: str = "",
    composer: str = "",
    catalog: str = "",
) -> dict[str, Any]:
    """Minimal non-polluting dossier after identity betrayal scrub (regen-safe)."""
    return {
        "work_title": work_title or "",
        "composer": composer or "",
        "catalog": catalog or "",
        "dossier_id": "",
        "listening_thesis": "",
        "work_introduction": "",
        "form": "",
        "width_points": [],
        "depth_points": [],
        "myths_and_caveats": [],
        "listening_map": [],
        "related_works": [],
        "interpretations": [],
        "appreciation_videos": [],
        "vinyl_and_discography": [],
        "zh": {},
        "zh_hans": {},
        "zh_hant": {},
        "_provenance": {"scrubbed_identity_pollution": True},
    }


def scrub_dossier_if_identity_polluted(
    dossier: dict[str, Any] | None,
    *,
    work_title: str = "",
    work_hint: str = "",
    raw_message: str = "",
    composer: str = "",
) -> tuple[dict[str, Any], bool]:
    """Return (dossier, scrubbed). Scrub to identity shell when betrayal detected."""
    d = dict(dossier or {})
    if not dossier_betrays_identity_lock(
        d, work_title=work_title or str(d.get("work_title") or ""),
        work_hint=work_hint,
        raw_message=raw_message,
    ):
        return d, False
    return (
        identity_shell_dossier(
            work_title=work_title or str(d.get("work_title") or ""),
            composer=composer or str(d.get("composer") or ""),
            catalog=str(d.get("catalog") or ""),
        ),
        True,
    )
