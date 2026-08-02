"""Identity hygiene gates — portrait / foreign-family dossier pollution (class-level).

Class rules: refuse KB/family layers whose instruments miss the locked title,
and portraits that name a different registered composer. No per-work branches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Avoid circular import with decontam — keep a local copy of the instrument-miss helper.


_SYNTH_ASSETS = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "aulos-listening-synthesize"
    / "assets"
)


@dataclass
class HygieneFinding:
    code: str
    note: str
    markers: list[str] = field(default_factory=list)


@dataclass
class HygieneReport:
    findings: list[HygieneFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def markers(self) -> list[str]:
        out: list[str] = []
        for f in self.findings:
            for m in f.markers:
                if m and m not in out:
                    out.append(m)
        return out


def family_instruments_miss_title(family: dict[str, Any], title_blob: str) -> bool:
    """True when family declares instruments and required evidence misses the title.

    SPEC-033: when the family names soloist-class instruments, ensemble-only hits
    (orchestra / strings) do not count — piano-concerto must see piano evidence.
    """
    from aulos_skills.instrument_evidence import (
        family_requires_soloist_evidence,
        family_soloist_misses_blob,
        token_hits_blob,
    )

    match = dict(family.get("match") or {})
    instruments = [str(t).lower() for t in (match.get("instruments") or []) if t]
    if not instruments:
        return False
    if family_requires_soloist_evidence(family):
        return family_soloist_misses_blob(family, title_blob)
    blob = title_blob.lower()
    for tok in instruments:
        if token_hits_blob(tok, blob):
            return False
    return True

@lru_cache(maxsize=1)
def _composer_cards() -> list[dict[str, Any]]:
    index_path = _SYNTH_ASSETS / "index.yaml"
    if not index_path.is_file():
        return []
    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    cards: list[dict[str, Any]] = []
    for entry in index.get("composers") or []:
        path = _SYNTH_ASSETS / "composers" / str(entry.get("path") or "")
        card: dict[str, Any] = {}
        if path.is_file():
            card = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        aliases = [str(a).lower() for a in (entry.get("aliases") or []) if a]
        name = str(card.get("composer") or entry.get("id") or "").lower()
        if name and name not in aliases:
            aliases.append(name)
        for a in list(card.get("aliases") or []):
            al = str(a).lower()
            if al and al not in aliases:
                aliases.append(al)
        cards.append(
            {
                "id": str(entry.get("id") or ""),
                "composer": str(card.get("composer") or entry.get("id") or ""),
                "aliases": aliases,
                "card": card,
            }
        )
    return cards


@lru_cache(maxsize=1)
def _family_index() -> dict[str, dict[str, Any]]:
    index_path = _SYNTH_ASSETS / "index.yaml"
    if not index_path.is_file():
        return {}
    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    out: dict[str, dict[str, Any]] = {}
    for entry in index.get("families") or []:
        fid = str(entry.get("id") or "")
        path = _SYNTH_ASSETS / "families" / str(entry.get("path") or "")
        if not fid or not path.is_file():
            continue
        family = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        out[fid] = family
    return out


def _composer_matches(composer: str, aliases: list[str]) -> bool:
    blob = (composer or "").lower()
    if not blob:
        return False
    return any(a and a in blob for a in aliases)


def portrait_betrays_composer(portrait: dict[str, Any] | None, composer: str) -> bool:
    """True when portrait caption/credit/url names a different registered composer."""
    if not isinstance(portrait, dict) or not portrait:
        return False
    composer_l = (composer or "").lower().strip()
    if not composer_l or composer_l in {"unknown", "unknown composer", "composer"}:
        return False
    blob = " ".join(
        str(portrait.get(k) or "")
        for k in ("image_url", "credit", "caption", "caption_zh", "credit_zh")
    ).lower()
    if not blob.strip():
        return False
    for card in _composer_cards():
        aliases = list(card.get("aliases") or [])
        if not aliases:
            continue
        if _composer_matches(composer_l, aliases):
            continue
        # Foreign composer named in portrait metadata
        if any(a and len(a) >= 4 and a in blob for a in aliases):
            return True
    return False


def family_forms_hit_title(family: dict[str, Any], title_blob: str) -> bool:
    """True when family declares forms and at least one appears in the title blob."""
    match = dict(family.get("match") or {})
    forms = [str(t).lower() for t in (match.get("forms") or []) if t]
    if not forms:
        return False
    blob = title_blob.lower()
    return any(t and t in blob for t in forms)


def foreign_family_id(
    dossier: dict[str, Any] | None,
    title_blob: str,
    *,
    composer: str = "",
) -> str | None:
    """Return family_id when dossier_id is family:* that does not belong on this shelf.

    Class rules:
    1. Composer-scoped family whose match.composers miss the locked composer → foreign
    2. Family instruments miss the title entirely → foreign, unless forms clearly hit
    3. Strong exclusive instruments required by family but absent from title → foreign
       even when a shared token like ``piano`` is present
    """
    did = str((dossier or {}).get("dossier_id") or "")
    if not did.startswith("family:"):
        return None
    fid = did.split(":", 1)[1].strip()
    if not fid:
        return None
    family = _family_index().get(fid) or {}
    if not family:
        return fid  # unknown family id still suspicious
    match = dict(family.get("match") or {})
    composer_tokens = [str(t).lower() for t in (match.get("composers") or []) if t]
    composer_l = (composer or "").lower()
    blob = title_blob.lower()
    if composer_tokens:
        composer_hit = any(
            t and (t in blob or t in composer_l) for t in composer_tokens
        )
        if not composer_hit:
            return fid
    forms_hit = family_forms_hit_title(family, title_blob)
    # SPEC-033: soloist miss is foreign even when forms hit (concerto ≠ piano-concerto).
    if family_instruments_miss_title(family, title_blob):
        from aulos_skills.instrument_evidence import family_requires_soloist_evidence

        if family_requires_soloist_evidence(family) or not forms_hit:
            return fid
    from aulos_skills.instrument_evidence import family_conflicts_blob_soloists

    if family_conflicts_blob_soloists(family, title_blob):
        return fid
    instruments = [str(t).lower() for t in (match.get("instruments") or []) if t]
    strong = [
        t
        for t in instruments
        if t
        in {
            "cello",
            "violoncello",
            "大提琴",
            "violin",
            "violon",
            "小提琴",
            "viola",
            "中提琴",
            "organ",
            "管风琴",
            "piano",
            "钢琴",
            "oboe",
            "双簧管",
        }
    ]
    if strong and not any(t in blob for t in strong):
        # Shared tokens (piano) must not keep a cello-duo pack on a piano concerto.
        return fid
    return None


def scrub_markers_for_family(family_id: str) -> list[str]:
    """Markers to scrub when a foreign family pack leaked into the dossier."""
    family = _family_index().get(family_id) or {}
    markers: list[str] = [f"family:{family_id}", family_id]
    match = dict(family.get("match") or {})
    for tok in match.get("instruments") or []:
        t = str(tok).lower().strip()
        if t and len(t) >= 4:
            markers.append(t)
    catalog = str(family.get("catalog") or "")
    for m in re.findall(r"op\.?\s*\d+", catalog, flags=re.I):
        markers.append(re.sub(r"\s+", "", m.lower()))
        markers.append(m.lower())
    # Derive scrub tokens from family prose fields (no per-family hardcoded lists)
    for key in ("listening_thesis", "work_introduction", "form"):
        blob = str(family.get(key) or "").lower()
        for tok in re.findall(r"[a-z][a-z\-]{3,}", blob):
            if tok in {"with", "from", "that", "this", "these", "into", "over", "under"}:
                continue
            if any(x in tok for x in ("cello", "violin", "piano", "duo", "suite", "sonata")):
                markers.append(tok)
    # Dedupe preserve order
    out: list[str] = []
    for m in markers:
        if m and m not in out:
            out.append(m)
    return out


def inspect_dossier_hygiene(
    dossier: dict[str, Any] | None,
    *,
    composer: str,
    work_title: str = "",
    raw_message: str = "",
) -> HygieneReport:
    """Deterministic hygiene findings for multi-agent review + scorecard."""
    d = dict(dossier or {})
    title_blob = f"{work_title} {composer} {raw_message}".lower()
    findings: list[HygieneFinding] = []

    portrait = d.get("composer_portrait") if isinstance(d.get("composer_portrait"), dict) else {}
    if portrait_betrays_composer(portrait, composer):
        findings.append(
            HygieneFinding(
                code="portrait_composer_mismatch",
                note="Composer portrait metadata names a different composer",
                markers=[],
            )
        )

    fid = foreign_family_id(d, title_blob, composer=composer)
    if fid:
        findings.append(
            HygieneFinding(
                code="foreign_family_dossier",
                note=f"dossier_id family:{fid} instruments miss locked title",
                markers=scrub_markers_for_family(fid),
            )
        )

    return HygieneReport(findings=findings)


def apply_identity_hygiene(
    dossier: dict[str, Any] | None,
    *,
    composer: str,
    work_title: str = "",
    raw_message: str = "",
) -> tuple[dict[str, Any], HygieneReport]:
    """Clear betraying portrait / foreign family id; return markers for scrubbers."""
    out = dict(dossier or {})
    report = inspect_dossier_hygiene(
        out, composer=composer, work_title=work_title, raw_message=raw_message
    )
    for finding in report.findings:
        if finding.code == "portrait_composer_mismatch":
            out["composer_portrait"] = {}
            zh = dict(out.get("zh") or {})
            if isinstance(zh.get("composer_portrait"), dict):
                zh["composer_portrait"] = {}
                out["zh"] = zh
                out["zh_hans"] = zh
        if finding.code == "foreign_family_dossier":
            did = str(out.get("dossier_id") or "")
            if did.startswith("family:"):
                out["dossier_id"] = ""
    return out, report


def html_title_matches_work(html: str, work_title: str) -> bool:
    """True when at least one <h1> shares a strong token with work_title (not video titles)."""
    if not html or not work_title:
        return True
    titles = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    if not titles:
        return True
    work_tokens = {
        t.lower()
        for t in re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", work_title, flags=re.I)
    }
    weak = {
        "the",
        "and",
        "for",
        "major",
        "minor",
        "piano",
        "concerto",
        "sonata",
        "orchestra",
        "mozart",
        "bach",
        "guide",
        "listening",
    }
    strong = work_tokens - weak
    if not strong:
        strong = work_tokens
    for raw in titles:
        text = re.sub(r"<[^>]+>", "", raw)
        text = re.sub(r"\s+", " ", text).strip().lower()
        # Appreciation-host titles (Bernstein on …) without catalog/work tokens
        if any(s in text for s in strong):
            return True
    return False
