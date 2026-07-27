"""Per-node decontamination: marker resolution, validation, rework hints (SPEC-009)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from aulos_skills.identity import load_catalog

DECONTAM_TRIGGERS = frozenset(
    {
        "listening.synthesize",
        "listening.width",
        "listening.depth",
        "listening.compose",
    }
)

_INSTRUMENT_SKIP = frozenset(
    {
        "cello",
        "violoncello",
        "大提琴",
        "piano",
        "钢琴",
        "keyboard",
        "violin",
        "violon",
        "小提琴",
        "orchestra",
        "交响",
        "solo",
        "duo",
        "suite",
        "suites",
        "sonata",
        "sonatas",
        "variation",
        "variations",
        "奏鸣",
        "变奏",
        "组曲",
    }
)

_MAX_MARKER_LEN = 48


@dataclass
class DecontamFinding:
    marker: str
    where: str


@dataclass
class DecontamReport:
    ok: bool
    findings: list[DecontamFinding] = field(default_factory=list)
    markers_used: list[str] = field(default_factory=list)
    foreign_family: str | None = None


def _title_blob(context: dict[str, Any]) -> str:
    return " ".join(
        str(x)
        for x in (
            context.get("work_title"),
            context.get("composer") or context.get("composer_guess"),
            context.get("raw_message"),
            context.get("work_hint"),
        )
        if x
    ).lower()


def catalog_alien_markers(
    *,
    work_title: str = "",
    composer: str = "",
    work_id: str | None = None,
    composer_id: str | None = None,
) -> list[str]:
    """Markers that must not appear as foreign chambers on this shelf."""
    cat = load_catalog()
    title_blob = f"{work_title} {composer}".lower()
    if work_id and work_id in cat.works:
        return list(cat.conflict_markers_for(cat.works[work_id]))

    markers: set[str] = set()
    composer_l = (composer or "").lower()
    composer_id_l = (composer_id or "").lower()

    for work in cat.works.values():
        same_id = bool(composer_id_l and work.composer_id == composer_id_l)
        card = cat.composers.get(work.composer_id)
        same_name = False
        if card and composer_l:
            names = [card.name_en, card.name_zh, *list(getattr(card, "aliases", None) or [])]
            same_name = any(n and str(n).lower() in composer_l for n in names if n)
        same_composer = same_id or same_name

        # Explicit scrub lists always apply
        for m in work.conflict_markers:
            ml = str(m).lower().strip()
            if ml and len(ml) >= 3 and ml not in title_blob:
                markers.add(ml)

        if same_composer:
            # Other works by same composer: only strong catalog / distinctive (not shared surname)
            for t in list(work.distinctive_tokens) + list(work.catalog_numbers):
                tl = str(t).lower().strip()
                if (
                    tl
                    and len(tl) >= 5
                    and tl not in title_blob
                    and tl not in cat.weak_tokens
                    and tl not in _INSTRUMENT_SKIP
                ):
                    markers.add(tl)
            continue

        # Foreign composer shelves — aliases / catalog / distinctive (skip bare instruments)
        for t in list(work.distinctive_tokens) + list(work.catalog_numbers) + list(work.aliases):
            tl = str(t).lower().strip()
            if (
                tl
                and 5 <= len(tl) <= _MAX_MARKER_LEN
                and tl not in title_blob
                and tl not in cat.weak_tokens
                and tl not in _INSTRUMENT_SKIP
            ):
                markers.add(tl)
        if card:
            for n in (card.name_en, card.name_zh, *list(getattr(card, "aliases", None) or [])):
                nl = str(n or "").lower().strip()
                if nl and len(nl) >= 4 and nl not in title_blob and nl not in cat.weak_tokens:
                    markers.add(nl)

    return sorted(markers)


def resolve_scrub_markers(context: dict[str, Any]) -> list[str]:
    title_blob = _title_blob(context)
    base = [str(m).lower() for m in (context.get("conflict_markers") or []) if m]
    aliens = catalog_alien_markers(
        work_title=str(context.get("work_title") or ""),
        composer=str(context.get("composer") or context.get("composer_guess") or ""),
        work_id=str(context.get("work_id") or "") or None,
        composer_id=str(context.get("composer_id") or "") or None,
    )
    out: list[str] = []
    seen: set[str] = set()
    for m in base + aliens:
        ml = m.lower().strip()
        if not ml or len(ml) < 3 or ml in seen:
            continue
        if ml in title_blob:
            continue
        seen.add(ml)
        out.append(ml)
    return out


def _blob_hits(blob: str, markers: list[str]) -> list[str]:
    low = blob.lower()
    return [m for m in markers if m and m in low]


def _dossier_blob(dossier: dict[str, Any]) -> str:
    if not dossier:
        return ""
    return json.dumps(dossier, ensure_ascii=False)


def family_instruments_miss_title(family: dict[str, Any], title_blob: str) -> bool:
    """True when family declares instruments and none appear in the title blob."""
    match = dict(family.get("match") or {})
    instruments = [str(t).lower() for t in (match.get("instruments") or []) if t]
    if not instruments:
        return False
    # Treat violon / violin as string-family peers of each other for miss detection
    blob = title_blob.lower()
    for tok in instruments:
        if tok and tok in blob:
            return False
        # "violoncello" should not count as hit for bare "violon"
        if tok in {"cello", "violoncello", "大提琴"} and (
            "cello" in blob or "violoncello" in blob or "大提琴" in blob
        ):
            return False
    return True


def _strip_ambient_for_scan(blob: str) -> str:
    """Remove ambient player blocks so intentional peer atmosphere is not a false positive."""
    if not blob:
        return ""
    out = blob
    out = re.sub(
        r"<aside\b[^>]*\bdata-ambient(?:-player)?\b[^>]*>[\s\S]*?</aside>",
        " ",
        out,
        flags=re.I,
    )
    out = re.sub(
        r'<section\b[^>]*id=["\']aulos-ambient["\'][^>]*>[\s\S]*?</section>',
        " ",
        out,
        flags=re.I,
    )
    out = re.sub(
        r'<script\b[^>]*id=["\']aulos-ambient[^"\']*["\'][^>]*>[\s\S]*?</script>',
        " ",
        out,
        flags=re.I,
    )
    return out


def validate_node_outputs(
    trigger: str,
    context: dict[str, Any],
    outputs: dict[str, Any],
    *,
    family: dict[str, Any] | None = None,
) -> DecontamReport:
    if trigger not in DECONTAM_TRIGGERS:
        return DecontamReport(ok=True)

    markers = resolve_scrub_markers(context)
    findings: list[DecontamFinding] = []
    foreign_family: str | None = None
    title_blob = _title_blob(context)

    if trigger == "listening.synthesize":
        src = str(outputs.get("synthesize_source") or context.get("synthesize_source") or "")
        fam = family or {}
        if "family:" in src and fam and family_instruments_miss_title(fam, title_blob):
            foreign_family = str(fam.get("family_id") or "unknown")
            findings.append(DecontamFinding(marker=f"family:{foreign_family}", where="synthesize_source"))
        dossier = dict(outputs.get("corpus_dossier") or {})
        # Exclude ambient — peer stand-ins may legally mention conflict-work tokens
        scan_doc = {k: v for k, v in dossier.items() if k != "ambient_audio"}
        zh = dict(scan_doc.get("zh") or scan_doc.get("zh_hans") or {})
        zh.pop("ambient_audio", None)
        if "zh" in scan_doc or zh:
            scan_doc["zh"] = zh
        scan_doc.pop("zh_hans", None)
        for where, blob in (
            ("corpus_dossier", _dossier_blob(scan_doc)),
            ("listening_thesis", str(dossier.get("listening_thesis") or "")),
            ("work_introduction", str(dossier.get("work_introduction") or "")),
            ("zh", _dossier_blob(zh)),
        ):
            for m in _blob_hits(blob, markers):
                findings.append(DecontamFinding(marker=m, where=where))

    elif trigger in ("listening.width", "listening.depth"):
        key = "width_dossier" if trigger.endswith("width") else "depth_dossier"
        dossier = dict(outputs.get(key) or {})
        scan = dict(dossier)
        if isinstance(scan.get("salon_dossier"), dict):
            salon = dict(scan["salon_dossier"])
            salon.pop("ambient_audio", None)
            zh = dict(salon.get("zh") or {})
            zh.pop("ambient_audio", None)
            salon["zh"] = zh
            scan["salon_dossier"] = salon
        for m in _blob_hits(_dossier_blob(scan), markers):
            findings.append(DecontamFinding(marker=m, where=key))

    elif trigger == "listening.compose":
        html = _strip_ambient_for_scan(str(outputs.get("guide_html") or ""))
        for m in _blob_hits(html, markers):
            findings.append(DecontamFinding(marker=m, where="guide_html"))

    # Deduplicate findings by marker+where
    uniq: list[DecontamFinding] = []
    seen_f: set[tuple[str, str]] = set()
    for f in findings:
        k = (f.marker, f.where)
        if k in seen_f:
            continue
        seen_f.add(k)
        uniq.append(f)

    return DecontamReport(
        ok=not uniq,
        findings=uniq[:40],
        markers_used=markers,
        foreign_family=foreign_family,
    )


def apply_rework_hints(context: dict[str, Any], report: DecontamReport) -> None:
    """Mutate context so the next node attempt refuses polluted layers."""
    merged = list(context.get("conflict_markers") or [])
    for m in report.markers_used:
        if m and m not in merged:
            merged.append(m)
    for f in report.findings:
        if f.marker and f.marker not in merged and not f.marker.startswith("family:"):
            merged.append(f.marker)
    context["conflict_markers"] = merged
    context["decontam_rework"] = True
    if report.foreign_family:
        context["refuse_families"] = True
        refused = list(context.get("refuse_family_ids") or [])
        if report.foreign_family not in refused:
            refused.append(report.foreign_family)
        context["refuse_family_ids"] = refused


def record_decontam_event(
    context: dict[str, Any],
    *,
    trigger: str,
    attempt: int,
    report: DecontamReport,
    repaired: bool,
) -> None:
    events = list(context.get("decontam_events") or [])
    events.append(
        {
            "trigger": trigger,
            "attempt": attempt,
            "ok": report.ok,
            "repaired": repaired,
            "foreign_family": report.foreign_family,
            "findings": [{"marker": f.marker, "where": f.where} for f in report.findings[:12]],
        }
    )
    context["decontam_events"] = events
    if not report.ok and not repaired:
        context["decontam_failed"] = True
        context["decontam_findings"] = [
            {"marker": f.marker, "where": f.where} for f in report.findings[:20]
        ]
