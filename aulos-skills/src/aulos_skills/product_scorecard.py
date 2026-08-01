"""Reader-facing ProductScorecard — separate from process diagnostics (SPEC-025)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aulos_skills.chamber_contracts import audit_chamber_contracts
from aulos_skills.prose_hygiene import is_mostly_cjk
from aulos_skills.salon_codex import coerce_dict, dossier_richness

SCHEMA = "aulos.product_scorecard/v1"
MAX_PER = 3


@dataclass
class ProductFinding:
    severity: str
    code: str
    note: str


@dataclass
class ProductScorecard:
    schema: str = SCHEMA
    dimensions: dict[str, int] = field(default_factory=dict)
    findings: list[ProductFinding] = field(default_factory=list)
    earned: int = 0
    max_possible: int = 18
    pct: float = 0.0
    band: str = "weak"
    pass_: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "dimensions": dict(self.dimensions),
            "findings": [
                {"severity": f.severity, "code": f.code, "note": f.note} for f in self.findings[:20]
            ],
            "rollup": {
                "earned": self.earned,
                "max_possible": self.max_possible,
                "pct": self.pct,
                "band": self.band,
                "pass": self.pass_,
            },
        }


def _clamp(n: int) -> int:
    return max(0, min(MAX_PER, n))


def _band(pct: float) -> str:
    if pct >= 85:
        return "strong"
    if pct >= 70:
        return "solid"
    if pct >= 50:
        return "fair"
    return "weak"


def score_product(
    *,
    html: str,
    context: dict[str, Any],
    dossier: dict[str, Any] | None = None,
) -> ProductScorecard:
    """Score what a listener reads — not pipeline node honesty."""
    d = dict(dossier or context.get("corpus_dossier") or {})
    html = html or str(context.get("guide_html") or "")
    html_l = html.lower()
    findings: list[ProductFinding] = []
    dims: dict[str, int] = {}

    # identity_clarity
    from aulos_skills.text_match import composers_compatible

    title = str(context.get("work_title") or d.get("work_title") or "")
    composer = str(context.get("composer") or d.get("composer") or "")
    work_id = str(context.get("work_id") or "")
    lock = dict(context.get("intent_lock") or {})
    locked_composer = str(lock.get("composer") or "").strip()
    id_score = 0
    if locked_composer and composer and not composers_compatible(locked_composer, composer):
        findings.append(
            ProductFinding(
                "high",
                "product_composer_drift",
                f"Composer drifted from IntentLock ({locked_composer} → {composer})",
            )
        )
        id_score = 0
    else:
        if title and "=" not in title and not title.lower().startswith("bartholdy"):
            id_score += 1
        else:
            findings.append(
                ProductFinding("high", "product_title_pollution", "Work title looks polluted or empty")
            )
        if composer and composer.lower() not in {"unknown", "unknown composer"}:
            id_score += 1
        if work_id or context.get("corpus_hit"):
            id_score += 1
    dims["identity_clarity"] = _clamp(id_score)

    # craft_richness
    rich = dossier_richness(d)
    craft = 0
    if rich >= 7:
        craft = 3
    elif rich >= 4:
        craft = 2
    elif rich >= 2:
        craft = 1
        findings.append(ProductFinding("medium", "product_craft_thin", f"Dossier richness={rich}"))
    else:
        findings.append(ProductFinding("high", "product_craft_empty", "Craft chambers nearly empty"))
    if len(d.get("listening_map") or []) >= 3 and len(d.get("width_points") or []) >= 3:
        craft = max(craft, 2)
    dims["craft_richness"] = _clamp(craft)

    # bilingual_parity
    zh = coerce_dict(d.get("zh") or d.get("zh_hans"))
    thesis = str(d.get("listening_thesis") or "").strip()
    zh_thesis = str(zh.get("listening_thesis") or "").strip()
    bi = 0
    if ('data-lang="en"' in html) and (
        'data-lang="zh' in html or "data-lang='zh" in html
    ):
        bi += 1
    if thesis and not is_mostly_cjk(thesis) and len(thesis) >= 40:
        bi += 1
    else:
        findings.append(ProductFinding("high", "product_en_thesis", "EN listening thesis missing or thin"))
    if zh_thesis and len(zh_thesis) >= 12:
        bi += 1
    else:
        findings.append(ProductFinding("high", "product_zh_thesis", "ZH listening thesis missing or thin"))
    dims["bilingual_parity"] = _clamp(bi)

    # prose_hygiene
    hyg = 3
    blob = f"{html}\n{thesis}\n{title}"
    if "CRITIQUE LOCK" in blob.upper() or "REVIEW REPAIR" in blob.upper():
        hyg = 0
        findings.append(ProductFinding("high", "product_process_leak", "Process locks visible in product prose"))
    elif is_mostly_cjk(thesis) and thesis:
        hyg = 1
        findings.append(ProductFinding("high", "product_en_cjk", "EN thesis mostly CJK"))
    dims["prose_hygiene"] = _clamp(hyg)

    # atelier_coverage
    atelier_needles = (
        ("composer-", "作曲家"),
        ("genesis-", "创作背景"),
        ("sound-", "声响世界"),
        ("interpretations-", "名家演绎"),
        ("anatomy-", "作品解剖"),
        ("practice-", "练习聆听"),
    )
    hits = 0
    for en, zh_lab in atelier_needles:
        if en in html_l or zh_lab in html:
            hits += 1
    if hits >= 5:
        atelier = 3
    elif hits >= 3:
        atelier = 2
    elif hits >= 1:
        atelier = 1
        findings.append(ProductFinding("medium", "product_atelier_thin", f"Atelier chambers present={hits}"))
    else:
        atelier = 0
        findings.append(ProductFinding("high", "product_atelier_empty", "No atelier chambers in HTML"))
    dims["atelier_coverage"] = _clamp(atelier)

    identity_resolved = bool(work_id or context.get("corpus_hit") or context.get("family_hints"))

    # asset_depth — systemic provenance (SPEC-026)
    prov = coerce_dict(d.get("_provenance"))
    dossier_id = str(d.get("dossier_id") or "")
    synth = str(context.get("synthesize_source") or "")
    has_craft = (
        dossier_id.startswith("craft:")
        or "craft:" in synth
        or bool(prov.get("craft_pack"))
    )
    has_catalog_floor = (
        dossier_id.startswith("catalog-floor:")
        or "catalog-floor:" in synth
        or bool(prov.get("catalog_craft_floor"))
    )
    has_knowledge = bool(
        prov.get("knowledge_thicken")
        or context.get("knowledge_thicken")
        or "knowledge-plane" in synth
    )
    kn_portrait = bool(coerce_dict(d.get("composer_portrait")).get("image_url"))
    has_family = dossier_id.startswith("family:") or "family:" in synth
    has_archetype = (
        dossier_id.startswith("archetype:")
        or dossier_id.startswith("dimension:")
        or "archetype:" in synth
        or "dimension:" in synth
        or bool(prov.get("unknown_case_thicken"))
        or bool(prov.get("dimension_template"))
    )
    asset = 0
    if has_craft or (has_knowledge and kn_portrait and (has_catalog_floor or has_craft)):
        asset = 3
    elif has_catalog_floor or (has_knowledge and (kn_portrait or coerce_dict(d.get("composer_profile")))):
        asset = 2
    elif has_family or has_archetype or rich >= 4:
        asset = 1
        if identity_resolved:
            findings.append(
                ProductFinding(
                    "medium",
                    "product_asset_family_only",
                    "Identity-resolved shelf still on family/archetype/scaffold thickness",
                )
            )
    else:
        if identity_resolved:
            findings.append(
                ProductFinding(
                    "high",
                    "product_asset_empty",
                    "No craft pack / catalog floor / knowledge thicken on resolved identity",
                )
            )
    dims["asset_depth"] = _clamp(asset)

    # Chamber contracts (identity-resolved shelves)
    for gap in audit_chamber_contracts(d, identity_resolved=identity_resolved):
        if gap.get("severity") == "high":
            findings.append(
                ProductFinding("high", str(gap.get("code") or "contract"), str(gap.get("note") or ""))
            )

    earned = sum(dims.values())
    max_possible = MAX_PER * len(dims)
    pct = round(100.0 * earned / max_possible, 1) if max_possible else 0.0
    band = _band(pct)
    # Family-only cannot claim strong on identity-resolved shelves
    if identity_resolved and dims.get("asset_depth", 0) <= 1 and band == "strong":
        band = "solid"
        findings.append(
            ProductFinding(
                "medium",
                "product_asset_cap",
                "Band capped to solid without catalog floor / craft / knowledge depth",
            )
        )
    high = [f for f in findings if f.severity == "high"]
    passed = band in {"solid", "strong"} and not high

    return ProductScorecard(
        dimensions=dims,
        findings=findings,
        earned=earned,
        max_possible=max_possible,
        pct=pct,
        band=band,
        pass_=passed,
    )
