"""Listening process scorecards — NodeScorecard + ProcessScorecard (SPEC-019)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aulos_skills.html_bits import point_texts
from aulos_skills.salon_codex import dossier_richness

SCHEMA = "aulos.process_scorecard/v1"
MAX_PER_DIM = 3

PROCESS_DIMS = (
    "identity",
    "fidelity",
    "richness",
    "source_hygiene",
    "bilingual",
    "ambient",
    "craft",
)

PRODUCT_DIMS = (
    "specificity",
    "ear_cues",
    "structure",
    "bilingual",
    "ambient",
    "craft",
)

# trigger -> applicable process dims (others N/A)
NODE_DIMS: dict[str, frozenset[str]] = {
    "listening.intake": frozenset({"identity"}),
    "listening.corpus": frozenset({"identity", "richness"}),
    "listening.synthesize": frozenset({"identity", "fidelity", "richness", "source_hygiene"}),
    "listening.width": frozenset({"identity", "fidelity", "richness", "bilingual"}),
    "listening.depth": frozenset({"identity", "fidelity", "richness"}),
    "listening.compose": frozenset(
        {"identity", "fidelity", "source_hygiene", "bilingual", "ambient", "craft"}
    ),
    "listening.external_review": frozenset({"identity", "fidelity", "specificity"}),
    "listening.revise": frozenset(
        {"identity", "fidelity", "source_hygiene", "bilingual", "ambient", "craft"}
    ),
    "listening.eval": frozenset({"identity", "fidelity", "bilingual", "ambient", "craft"}),
}

SCORED_TRIGGERS = frozenset(NODE_DIMS.keys())


@dataclass
class Finding:
    severity: str
    code: str
    note: str

    def to_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "note": self.note}


@dataclass
class NodeScorecard:
    trigger: str
    scores: dict[str, int] = field(default_factory=dict)
    na_dims: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    hard_fail: bool = False
    layer: str = "node"

    @property
    def earned(self) -> int:
        return sum(int(v) for v in self.scores.values())

    @property
    def max_possible(self) -> int:
        return MAX_PER_DIM * len(self.scores)

    @property
    def pct(self) -> float:
        if self.max_possible <= 0:
            return 0.0
        return round(100.0 * self.earned / self.max_possible, 1)

    @property
    def band(self) -> str:
        return band_for_pct(self.pct)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "layer": self.layer,
            "scores": dict(self.scores),
            "na_dims": list(self.na_dims),
            "earned": self.earned,
            "max_possible": self.max_possible,
            "pct": self.pct,
            "band": self.band,
            "findings": [f.to_dict() for f in self.findings],
            "hard_fail": self.hard_fail,
        }


def band_for_pct(pct: float) -> str:
    if pct >= 85:
        return "strong"
    if pct >= 70:
        return "solid"
    if pct >= 55:
        return "developing"
    return "weak"


def _clamp(score: int) -> int:
    return max(0, min(MAX_PER_DIM, int(score)))


def _dossier_blob(context: dict[str, Any], outputs: dict[str, Any]) -> dict[str, Any]:
    if outputs.get("corpus_dossier"):
        return dict(outputs["corpus_dossier"])
    width = dict(outputs.get("width_dossier") or context.get("width_dossier") or {})
    if width.get("salon_dossier"):
        return dict(width["salon_dossier"])
    if context.get("corpus_dossier"):
        return dict(context["corpus_dossier"])
    return {}


def _score_identity(context: dict[str, Any], outputs: dict[str, Any]) -> tuple[int, list[Finding], bool]:
    findings: list[Finding] = []
    hard = False
    lock = dict(context.get("intent_lock") or outputs.get("intent_lock") or {})
    title = str(
        lock.get("work_title")
        or outputs.get("work_title")
        or context.get("work_title")
        or ""
    ).strip()
    composer = str(
        lock.get("composer")
        or outputs.get("composer")
        or outputs.get("composer_guess")
        or context.get("composer")
        or context.get("composer_guess")
        or ""
    ).strip()
    work_id = str(lock.get("work_id") or outputs.get("work_id") or context.get("work_id") or "")
    score = 0
    if title and title.lower() not in {"unspecified classical work", "classical work"}:
        score += 1
    else:
        findings.append(Finding("high", "identity_title", "Work title not locked"))
    # Packaging bleed (Discogs multi-lang dump / truncated Ges) is not a locked title
    if title and (
        ("=" in title and "/" in title)
        or re.search(r"(?i)/\s*(ges|rom)\s*$", title)
        or title.lower().startswith("bartholdy ")
    ):
        findings.append(
            Finding("high", "identity_packaging_title", "Work title looks like Discogs packaging dump")
        )
        hard = True
        score = min(score, 1)
    if composer and composer.lower() not in {"unknown", "unknown composer", "composer"}:
        score += 1
    else:
        findings.append(Finding("medium", "identity_composer", "Composer weak or missing"))
    if lock.get("work_title") or work_id or lock.get("catalog_numbers"):
        score += 1
    else:
        findings.append(Finding("medium", "identity_lock", "IntentLock thin (no numbers/work_id)"))

    # Guide #48 class: portrait / foreign family dossier_id betray lock → hard fail
    from aulos_skills.identity_hygiene import inspect_dossier_hygiene

    dossier = _dossier_blob(context, outputs)
    hygiene = inspect_dossier_hygiene(
        dossier,
        composer=composer,
        work_title=title,
        raw_message=str(context.get("raw_message") or ""),
    )
    for hf in hygiene.findings:
        findings.append(Finding("high", hf.code, hf.note))
        hard = True
        score = min(score, 1)

    html = str(outputs.get("guide_html") or context.get("guide_html") or "")
    if html:
        from aulos_skills.identity_hygiene import html_title_matches_work

        if not html_title_matches_work(html, title):
            findings.append(
                Finding("high", "html_title_drift", "Guide H1 drifted from locked work_title")
            )
            hard = True
            score = min(score, 1)

    # SPEC-034 / META-001 §4.1 — Discogs multi-work structure readiness on intake+identity
    from aulos_skills.release_structure import (
        assert_structure_ready,
        is_multi_work_program,
        structure_from_context,
    )

    st = structure_from_context({**context, **outputs})
    if is_multi_work_program(st):
        fails = list(outputs.get("structure_hard_fails") or context.get("structure_hard_fails") or [])
        if not fails:
            fails = assert_structure_ready(st)
        if fails or not st.get("structure_ready"):
            findings.append(
                Finding(
                    "high",
                    "release_structure_not_ready",
                    "Multi-work Discogs pressing lacks a coherent program map before deepen",
                )
            )
            hard = True
            score = min(score, 1)
        elif len(st.get("program") or []) >= 2:
            # Program recognized — strengthen lock signal
            score = min(3, score + 0)  # keep clamp path; presence already scored via catalogs
            if lock.get("catalog_numbers") or st.get("catalog_numbers_all"):
                score = max(score, 2)

    return _clamp(score), findings, hard


def _review_failed_for_trigger(context: dict[str, Any], trigger: str) -> bool:
    if context.get("review_failed"):
        return True
    for ev in context.get("review_events") or []:
        if not isinstance(ev, dict):
            continue
        if ev.get("trigger") != trigger:
            continue
        if not ev.get("ok") and not ev.get("repaired"):
            return True
    return False


def _score_fidelity(context: dict[str, Any], trigger: str) -> tuple[int, list[Finding], bool]:
    findings: list[Finding] = []
    hard = False
    if context.get("decontam_failed") or _review_failed_for_trigger(context, trigger):
        findings.append(
            Finding("high", "fidelity_fail", "Review/decontam failed — 本意偏离或污染未清")
        )
        return 0, findings, True
    # Look for unrepaired fail on this trigger; repaired counts as partial
    repaired = False
    for ev in context.get("review_events") or []:
        if isinstance(ev, dict) and ev.get("trigger") == trigger and ev.get("repaired"):
            repaired = True
    if repaired:
        findings.append(Finding("low", "fidelity_rework", "Review rework repaired drift"))
        return 2, findings, False
    # Clean path
    score = 3
    if context.get("critique_corrections"):
        score = 2
        findings.append(Finding("low", "fidelity_corrections", "Critique corrections present"))
    return score, findings, hard


def _score_richness(context: dict[str, Any], outputs: dict[str, Any]) -> tuple[int, list[Finding]]:
    findings: list[Finding] = []
    dossier = _dossier_blob(context, outputs)
    if outputs.get("depth_dossier"):
        depth = dict(outputs["depth_dossier"])
        # Merge depth coverage into richness probe
        rich = dossier_richness({**dossier, **{k: depth.get(k) for k in ("depth_points", "listening_map")}})
    else:
        rich = dossier_richness(dossier)
    if rich >= 7:
        return 3, findings
    if rich >= 4:
        return 2, findings
    if rich >= 2:
        findings.append(Finding("medium", "richness_thin", f"Dossier richness={rich}"))
        return 1, findings
    findings.append(Finding("high", "richness_empty", "Dossier chambers nearly empty"))
    return 0, findings


def _score_source_hygiene(context: dict[str, Any], outputs: dict[str, Any]) -> tuple[int, list[Finding]]:
    findings: list[Finding] = []
    dossier = _dossier_blob(context, outputs)
    html = str(outputs.get("guide_html") or context.get("guide_html") or "")
    caveats = list(dossier.get("myths_and_caveats") or [])
    score = 1  # baseline if we got here without hard pollution
    if caveats:
        score += 1
    else:
        findings.append(Finding("low", "hygiene_caveats", "No myths/caveats chamber"))
    aliens = list(
        (context.get("intent_lock") or {}).get("alien_markers")
        or context.get("conflict_markers")
        or []
    )
    from aulos_skills.decontam import marker_in_text

    scan = html + " " + str(dossier.get("listening_thesis") or "")
    hits = [m for m in aliens if m and marker_in_text(str(m), scan)]
    if hits:
        findings.append(
            Finding("high", "hygiene_alien", "Alien markers still visible: " + ", ".join(hits[:3]))
        )
        return 0, findings
    if context.get("refuse_topics") or context.get("critique_corrections"):
        score = min(3, score + 1)
    elif score >= 2:
        score = 3
    return _clamp(score), findings


def _has_bilingual(context: dict[str, Any], outputs: dict[str, Any]) -> bool:
    html = str(outputs.get("guide_html") or context.get("guide_html") or "")
    if (
        ('data-lang="zh-Hans"' in html or 'data-lang="zh-Hant"' in html or 'data-lang="zh"' in html)
        and 'data-lang="en"' in html
    ):
        return True
    dossier = _dossier_blob(context, outputs)
    zh = dossier.get("zh") or dossier.get("zh_hans") or dossier.get("zh_hant")
    return isinstance(zh, dict) and bool(zh)


def _score_bilingual(context: dict[str, Any], outputs: dict[str, Any]) -> tuple[int, list[Finding]]:
    findings: list[Finding] = []
    if not _has_bilingual(context, outputs):
        findings.append(Finding("medium", "bilingual_missing", "Missing zh/en bilingual surface"))
        return 0, findings
    # Pane presence is not enough — require ZH craft parity when EN craft exists.
    dossier = _dossier_blob(context, outputs)
    zh = dossier.get("zh") or dossier.get("zh_hans") or dossier.get("zh_hant") or {}
    if not isinstance(zh, dict):
        zh = {}
    en_map = list(dossier.get("listening_map") or [])
    zh_map = list(zh.get("listening_map") or [])
    en_width = list(dossier.get("width_points") or [])
    zh_width = list(zh.get("width_points") or [])
    en_thesis = str(dossier.get("listening_thesis") or "").strip()
    zh_thesis = str(zh.get("listening_thesis") or "").strip()
    from aulos_skills.prose_hygiene import is_mostly_cjk

    if en_thesis and is_mostly_cjk(en_thesis):
        findings.append(
            Finding("high", "en_layer_cjk_pollution", "EN listening_thesis is mostly CJK")
        )
        return 1, findings
    thin_zh = bool(en_thesis) and not zh_thesis and (len(en_map) >= 2 or len(en_width) >= 2)
    if thin_zh or (len(en_map) >= 2 and len(zh_map) == 0 and len(en_width) >= 2 and len(zh_width) == 0):
        findings.append(
            Finding(
                "medium",
                "bilingual_parity_thin",
                "ZH pane exists but craft chambers (map/width/thesis) lack parity with EN",
            )
        )
        return 2, findings
    return 3, findings


def _score_ambient(context: dict[str, Any], outputs: dict[str, Any]) -> tuple[int, list[Finding], bool]:
    findings: list[Finding] = []
    if _has_ambient(context, outputs):
        return 3, findings, False
    findings.append(Finding("medium", "ambient_missing", "Ambient player missing (soft gate)"))
    return 0, findings, False


def _has_ambient(context: dict[str, Any], outputs: dict[str, Any]) -> bool:
    html = str(outputs.get("guide_html") or context.get("guide_html") or "")
    if 'id="aulos-ambient"' in html or "data-ambient-player" in html:
        return True
    dossier = _dossier_blob(context, outputs)
    return bool(dossier.get("ambient_audio") or context.get("ambient_audio"))


def _score_craft_html(context: dict[str, Any], outputs: dict[str, Any]) -> tuple[int, list[Finding]]:
    findings: list[Finding] = []
    html = str(outputs.get("guide_html") or context.get("guide_html") or "")
    html_l = html.lower()
    score = 0
    if "<!DOCTYPE html>" in html:
        score += 1
    else:
        findings.append(Finding("medium", "craft_shell", "Guide HTML shell incomplete"))
    if "Fraunces" in html or "Noto Serif SC" in html:
        score += 1
    atelier_hits = sum(
        1
        for en_id, zh in (
            ("id='composer-", "作曲家"),
            ("id='genesis-", "创作背景与时代"),
            ("id='stature-", "何以传世"),
            ("id='sound-", "声响世界"),
        )
        if en_id in html_l or zh in html
    )
    if atelier_hits >= 3:
        score += 1
    elif html:
        findings.append(Finding("medium", "craft_chambers", "Atelier chambers thin"))
    return _clamp(score), findings


def score_node(
    trigger: str,
    context: dict[str, Any],
    outputs: dict[str, Any] | None = None,
) -> NodeScorecard | None:
    """Score one listening skill node. Returns None for unscored triggers (e.g. route)."""
    if trigger not in SCORED_TRIGGERS:
        return None
    outputs = dict(outputs or {})
    applicable = NODE_DIMS[trigger]
    na = [d for d in PROCESS_DIMS if d not in applicable]
    scores: dict[str, int] = {}
    findings: list[Finding] = []
    hard_fail = False

    if "identity" in applicable:
        s, f, hard = _score_identity(context, outputs)
        scores["identity"] = s
        findings.extend(f)
        hard_fail = hard_fail or hard
    if "fidelity" in applicable:
        s, f, hard = _score_fidelity(context, trigger)
        scores["fidelity"] = s
        findings.extend(f)
        hard_fail = hard_fail or hard
    if "richness" in applicable:
        s, f = _score_richness(context, outputs)
        scores["richness"] = s
        findings.extend(f)
    if "source_hygiene" in applicable:
        s, f = _score_source_hygiene(context, outputs)
        scores["source_hygiene"] = s
        findings.extend(f)
        if s == 0:
            hard_fail = True
    if "bilingual" in applicable:
        s, f = _score_bilingual(context, outputs)
        scores["bilingual"] = s
        findings.extend(f)
    if "ambient" in applicable:
        s, f, hard = _score_ambient(context, outputs)
        scores["ambient"] = s
        findings.extend(f)
        hard_fail = hard_fail or hard
    if "craft" in applicable:
        s, f = _score_craft_html(context, outputs)
        scores["craft"] = s
        findings.extend(f)

    return NodeScorecard(
        trigger=trigger,
        scores=scores,
        na_dims=na,
        findings=findings,
        hard_fail=hard_fail,
    )


def record_node_scorecard(
    context: dict[str, Any],
    trigger: str,
    outputs: dict[str, Any] | None = None,
) -> NodeScorecard | None:
    card = score_node(trigger, context, outputs)
    if card is None:
        return None
    cards = list(context.get("node_scorecards") or [])
    # Replace prior card for same trigger (rework)
    cards = [c for c in cards if not (isinstance(c, dict) and c.get("trigger") == trigger)]
    cards.append(card.to_dict())
    context["node_scorecards"] = cards
    # Self-improvement: high-severity scorecard findings → critique corrections for next rework
    if card.hard_fail or any(f.severity == "high" for f in card.findings):
        corrections = list(context.get("critique_corrections") or [])
        for f in card.findings:
            if f.severity != "high":
                continue
            note = f"{f.code}: {f.note}"
            if note not in corrections:
                corrections.append(note)
        context["critique_corrections"] = corrections[:12]
        if card.hard_fail:
            context["scorecard_hard_fail"] = True
    return card


def score_product(context: dict[str, Any]) -> dict[str, Any]:
    """Map existing eval probes onto 0–3 product dimensions."""
    html = str(context.get("guide_html") or "")
    html_l = html.lower()
    depth_points = point_texts((context.get("depth_dossier") or {}).get("depth_points") or [])
    listening_map = list((context.get("depth_dossier") or {}).get("listening_map") or [])
    findings: list[dict[str, str]] = []
    scores: dict[str, int] = {}
    hard_fail = False

    # specificity
    if len(depth_points) >= 3 and ("var" in html_l or "form" in html_l or len(listening_map) >= 2):
        scores["specificity"] = 3
    elif depth_points:
        scores["specificity"] = 2
        findings.append({"severity": "low", "code": "specificity", "note": "Add more landmarks"})
    else:
        scores["specificity"] = 0
        findings.append({"severity": "high", "code": "specificity", "note": "Missing depth specificity"})

    # ear cues
    earish = sum(
        1 for p in depth_points if any(w in p.lower() for w in ("listen", "hear", "notice", "track", "lock"))
    )
    earish += sum(1 for m in listening_map if isinstance(m, dict) and "cue" in m)
    if earish >= 3 and listening_map:
        scores["ear_cues"] = 3
    elif earish or listening_map:
        scores["ear_cues"] = 2
    else:
        scores["ear_cues"] = 0
        findings.append({"severity": "high", "code": "ear_cues", "note": "No ear-actionable cues"})

    # structure / atelier
    atelier_pairs = (
        ("id='composer-", "作曲家"),
        ("id='genesis-", "创作背景与时代"),
        ("id='stature-", "何以传世"),
        ("id='sound-", "声响世界"),
        ("id='interpretations-", "名家演绎"),
        ("id='media-", "聆听室"),
    )
    atelier_hits = sum(1 for en_id, zh in atelier_pairs if en_id in html_l or zh in html)
    needed = ("listening map", "聆听地图", "practice", "练习聆听", "composer", "作曲家", "anatomy", "作品解剖")
    structure_hits = sum(1 for n in needed if n in html_l or n in html)
    if atelier_hits >= 4 and structure_hits >= 4:
        scores["structure"] = 3
    elif atelier_hits >= 2 or structure_hits >= 2:
        scores["structure"] = 2
    else:
        scores["structure"] = 0
        findings.append({"severity": "high", "code": "structure", "note": "Salon chambers thin"})

    bilingual = _has_bilingual(context, {})
    scores["bilingual"] = 3 if bilingual else 0
    if not bilingual:
        findings.append({"severity": "medium", "code": "bilingual", "note": "Missing bilingual panes"})

    ambient_ok = _has_ambient(context, {})
    scores["ambient"] = 3 if ambient_ok else 0
    if not ambient_ok:
        findings.append({"severity": "medium", "code": "ambient", "note": "Missing ambient player (soft)"})
        # SPEC-006: absence is soft — no hard_fail solely for missing ambient.

    craft_s, craft_f = _score_craft_html(context, {})
    scores["craft"] = craft_s
    findings.extend(f.to_dict() for f in craft_f)

    if context.get("review_failed") or context.get("decontam_failed"):
        hard_fail = True

    earned = sum(scores.values())
    max_possible = MAX_PER_DIM * len(PRODUCT_DIMS)
    pct = round(100.0 * earned / max_possible, 1) if max_possible else 0.0
    return {
        "scores": scores,
        "earned": earned,
        "max_possible": max_possible,
        "pct": pct,
        "band": band_for_pct(pct),
        "findings": findings,
        "hard_fail": hard_fail,
    }


def rollup_process(context: dict[str, Any]) -> dict[str, Any]:
    """Build ProcessScorecard from accumulated node cards + product eval."""
    nodes = [c for c in (context.get("node_scorecards") or []) if isinstance(c, dict)]
    # Ensure eval node card present if missing
    if not any(c.get("trigger") == "listening.eval" for c in nodes):
        eval_card = score_node("listening.eval", context, {})
        if eval_card is not None:
            nodes = list(nodes) + [eval_card.to_dict()]

    product = score_product(context)
    earned = sum(int(c.get("earned") or 0) for c in nodes) + int(product.get("earned") or 0)
    max_possible = sum(int(c.get("max_possible") or 0) for c in nodes) + int(
        product.get("max_possible") or 0
    )
    pct = round(100.0 * earned / max_possible, 1) if max_possible else 0.0
    hard_fail = bool(product.get("hard_fail")) or any(bool(c.get("hard_fail")) for c in nodes)
    ambient_ok = _has_ambient(context, {})
    gates = {
        "eval_pass": bool(context.get("pass", False)) and not hard_fail,
        "review_failed": bool(context.get("review_failed")),
        "decontam_failed": bool(context.get("decontam_failed")),
        "ambient_ok": ambient_ok,
    }
    # Align eval_pass with legacy: if context already computed pass, prefer that for gate
    if "pass" in context:
        gates["eval_pass"] = bool(context.get("pass")) and not bool(context.get("review_failed"))

    return {
        "schema": SCHEMA,
        "nodes": nodes,
        "product": product,
        "rollup": {
            "earned": earned,
            "max_possible": max_possible,
            "pct": pct,
            "band": band_for_pct(pct),
            "hard_fail": hard_fail,
        },
        "gates": gates,
    }


def legacy_eval_from_product(product: dict[str, Any], context: dict[str, Any]) -> tuple[int, bool]:
    """Map product scorecard back to roughly compatible eval_score (0–10) + pass."""
    pct = float(product.get("pct") or 0)
    # Scale 0–100 → ~0–10
    score = int(round(pct / 10.0))
    score = max(0, min(10, score))
    ambient_ok = _has_ambient(context, {})
    if not ambient_ok:
        score = min(score, 9)
        # Soft: do not force fail solely for missing ambient (SPEC-006).
    if context.get("review_failed") or context.get("decontam_failed") or product.get("hard_fail"):
        score = min(score, 7)
        return score, False
    rich_identity = bool(
        context.get("corpus_hit")
        or context.get("synthesize_hit")
        or context.get("family_hints")
        or context.get("work_id")
    )
    structure = int((product.get("scores") or {}).get("structure") or 0)
    if rich_identity and structure < 2:
        score = min(score, 7)
        return score, False
    return score, score >= 8
