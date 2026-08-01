"""Expert music-guide / music-analysis external review (SPEC-022Δ / REQ-012).

Perspective: senior 音乐导赏专家 + 音乐分析专家 — find hard flaws (硬伤) in the
finished draft and emit required corrections for revise. Not a source-hunt pass.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from aulos_skills.identity_hygiene import (
    html_title_matches_work,
    inspect_dossier_hygiene,
)
from aulos_skills.identity_lock import dossier_betrays_identity_lock

SCHEMA = "aulos.external_review/v1"
ROUNDS_SCHEMA = "aulos.generation_rounds/v2"
PERSPECTIVE = "music_guide_and_analysis_expert"

LlmComplete = Callable[[str], str | None]

def _findings_from_hygiene(
    dossier: dict[str, Any],
    *,
    composer: str,
    work_title: str,
    raw_message: str,
    html: str,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    hygiene = inspect_dossier_hygiene(
        dossier, composer=composer, work_title=work_title, raw_message=raw_message
    )
    for hf in hygiene.findings:
        findings.append(
            {
                "severity": "high",
                "code": hf.code,
                "note": hf.note,
                "evidence": ",".join(hf.markers[:6]),
                "kind": "hard_flaw",
            }
        )
    if html and not html_title_matches_work(html, work_title):
        findings.append(
            {
                "severity": "high",
                "code": "html_title_drift",
                "note": "Guide H1 does not match locked work_title (title stolen or wrong work)",
                "evidence": "h1",
                "kind": "hard_flaw",
            }
        )
    if dossier_betrays_identity_lock(
        dossier, work_title=work_title, work_hint="", raw_message=raw_message
    ):
        findings.append(
            {
                "severity": "high",
                "code": "intent_betrayal",
                "note": "Dossier narrative drifted from IntentLock / catalog form family",
                "evidence": "dossier",
                "kind": "hard_flaw",
            }
        )
    return findings


def _expert_hard_flaw_findings(
    *,
    work_title: str,
    composer: str,
    html: str,
    dossier: dict[str, Any],
) -> list[dict[str, str]]:
    """Deterministic craft / analysis 硬伤 from draft HTML + dossier (no source hunt)."""
    from aulos_skills.identity_lock import identity_lock_alien_markers

    findings: list[dict[str, str]] = []
    title_l = (work_title or "").lower()
    html_l = (html or "").lower()
    blob = f"{title_l} {html_l}"

    # H1 must share strong tokens with locked work (class gate — no celebrity name list)
    if html and work_title and not html_title_matches_work(html, work_title):
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html or "", flags=re.I | re.S)
        h1 = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
        findings.append(
            {
                "severity": "high",
                "code": "h1_title_drift",
                "note": f"H1 does not match locked work title: {h1[:80]}",
                "evidence": "h1",
                "kind": "hard_flaw",
            }
        )

    # Form-lock aliens in HTML (data-driven policy — not per-work marker tuples)
    aliens = identity_lock_alien_markers(work_title=work_title, work_hint="")
    alien_hits = [m for m in aliens if m and m.lower() in html_l]
    if alien_hits:
        findings.append(
            {
                "severity": "high",
                "code": "foreign_chamber_in_guide",
                "note": "Guide body contains form-lock alien rhetoric for the locked title",
                "evidence": ",".join(alien_hits[:6]),
                "kind": "hard_flaw",
            }
        )

    # Guide craft: listening map / anatomy missing → analysis 硬伤 for a listening guide
    has_map = ("listening map" in html_l) or ("聆听地图" in html) or ("data-section=\"map\"" in html_l)
    has_anatomy = ("anatomy" in html_l) or ("作品解剖" in html) or ("listening landmarks" in html_l)
    if html and not has_map:
        findings.append(
            {
                "severity": "medium",
                "code": "missing_listening_map",
                "note": "导赏缺少可执行的聆听地图 / Listening Map — 分析专家视角硬伤",
                "evidence": "structure",
                "kind": "hard_flaw",
            }
        )
    if html and not has_anatomy and len(html) > 800:
        findings.append(
            {
                "severity": "medium",
                "code": "missing_anatomy",
                "note": "导赏缺少作品解剖 / form landmarks — 音乐分析专家视角硬伤",
                "evidence": "structure",
                "kind": "hard_flaw",
            }
        )

    # Dossier form vs title (concerto vs sonata / scale)
    form = str(dossier.get("form") or "").lower()
    if form:
        if "concerto" in title_l and "sonata" in form and "concerto" not in form:
            findings.append(
                {
                    "severity": "high",
                    "code": "form_title_mismatch",
                    "note": f"Locked title is a concerto but dossier form is '{form}'",
                    "evidence": form,
                    "kind": "hard_flaw",
                }
            )
        if "sonata" in title_l and "concerto" in form and "sonata" not in form:
            findings.append(
                {
                    "severity": "high",
                    "code": "form_title_mismatch",
                    "note": f"Locked title is a sonata but dossier form is '{form}'",
                    "evidence": form,
                    "kind": "hard_flaw",
                }
            )
        lyric_forms = (
            "songs without words",
            "lieder ohne worte",
            "nocturne",
            "mazurka",
            "prelude",
            "无词歌",
            "无言歌",
        )
        if "large-scale" in form and any(t in title_l for t in lyric_forms):
            findings.append(
                {
                    "severity": "high",
                    "code": "form_scale_mismatch",
                    "note": (
                        "Locked title is a lyric miniature / cycle but dossier form "
                        f"still says large-scale: '{form}'"
                    ),
                    "evidence": form,
                    "kind": "hard_flaw",
                }
            )

    # Process tags must never appear in product HTML / thesis
    if re.search(r"(?i)\b(CRITIQUE\s*LOCK|REVIEW\s*REPAIR)\b", blob):
        findings.append(
            {
                "severity": "high",
                "code": "process_lock_in_product_prose",
                "note": "Guide or thesis still contains CRITIQUE LOCK / REVIEW REPAIR process tags",
                "evidence": "process_lock",
                "kind": "hard_flaw",
            }
        )
    if ("=" in (work_title or "") and "/" in (work_title or "")) or re.search(
        r"(?i)/\s*(ges|rom)\s*$", work_title or ""
    ):
        findings.append(
            {
                "severity": "high",
                "code": "packaging_title_pollution",
                "note": "IntentLock work_title looks like Discogs packaging / truncated language dump",
                "evidence": (work_title or "")[:120],
                "kind": "hard_flaw",
            }
        )

    # Bilingual layer split: EN thesis mostly CJK while zh layer empty or divergent
    thesis = str(dossier.get("listening_thesis") or "")
    zh = dict(dossier.get("zh") or dossier.get("zh_hans") or {})
    from aulos_skills.prose_hygiene import is_mostly_cjk

    if thesis and is_mostly_cjk(thesis) and not str(zh.get("listening_thesis") or "").strip():
        findings.append(
            {
                "severity": "high",
                "code": "en_layer_cjk_pollution",
                "note": "EN listening_thesis is mostly CJK — bilingual layers not partitioned",
                "evidence": "listening_thesis",
                "kind": "hard_flaw",
            }
        )

    return findings


def _chamber_inventory(dossier: dict[str, Any]) -> dict[str, Any]:
    """Compact chamber presence so review LLM cannot claim 'empty guide' falsely."""
    inv: dict[str, Any] = {}
    for key in (
        "listening_thesis",
        "work_introduction",
        "form",
        "composer_portrait",
        "genesis",
        "sound_world",
        "width_points",
        "depth_points",
        "listening_map",
        "practice_notes",
        "interpretations",
        "myths_and_caveats",
    ):
        val = dossier.get(key)
        if isinstance(val, list):
            inv[key] = {"n": len(val), "sample": str(val[0])[:120] if val else ""}
        elif isinstance(val, dict):
            inv[key] = {"keys": list(val.keys())[:8], "n": len(val)}
        elif isinstance(val, str):
            inv[key] = {"chars": len(val), "sample": val[:160]}
        else:
            inv[key] = {"present": bool(val)}
    zh = dossier.get("zh") or dossier.get("zh_hans")
    if isinstance(zh, dict):
        inv["zh_thesis_chars"] = len(str(zh.get("listening_thesis") or ""))
    return inv


def _expert_llm_prompt(
    *,
    work_title: str,
    composer: str,
    html: str,
    dossier: dict[str, Any],
    prior_findings: list[dict[str, str]],
) -> str:
    from aulos_skills.prose_hygiene import strip_ambient_from_html

    review_html = strip_ambient_from_html(html)
    dossier_slim = {
        "form": dossier.get("form"),
        "catalog": dossier.get("catalog"),
        "era": dossier.get("era"),
        "listening_thesis": str(dossier.get("listening_thesis") or "")[:400],
        "work_introduction": str(dossier.get("work_introduction") or "")[:400],
        "dossier_id": dossier.get("dossier_id"),
        "composer_portrait": dossier.get("composer_portrait"),
        "chamber_inventory": _chamber_inventory(dossier),
    }
    return (
        "你是资深「音乐导赏专家」与「音乐分析专家」。只做导赏稿硬伤审查，不要去核对或搜集外部信息源。\n"
        "视角：作品身份、曲式/体裁、编制、乐章结构、聆听地图可执行性、肖像/标题是否张冠李戴、"
        "是否窜入无关作品（如协奏曲里写大提琴奏鸣曲）、中英文层是否混用、"
        "是否泄露 CRITIQUE LOCK/REVIEW REPAIR 等过程标签、Discogs 包装标题是否污染 IntentLock。\n"
        "Ambient 播放器 chrome 已从 HTML 中剥离 — 不要因缺少 ambient 控件就报告「只有 ambient、无导赏正文」。\n"
        "若 chamber_inventory 显示 thesis/map/points 已有内容，禁止报告 MISSING_GUIDE_CONTENT / empty body。\n"
        "不要报告「信息源不足」「网页未覆盖 K 编号」这类 source-hunt 问题。\n"
        "Return ONLY JSON:\n"
        '{"verdict":"PASS"|"REVISE"|"FAIL","summary":"…",'
        '"findings":[{"severity":"high|medium|low","code":"…","note":"…","evidence":"…","kind":"hard_flaw"}],'
        '"required_corrections":["具体可执行的修复指令…"]}\n'
        "high = 硬伤必须修；medium = 分析/导赏结构明显缺陷；PASS 仅当无硬伤。\n"
        f"IntentLock work={work_title!r} composer={composer!r}\n"
        f"Dossier slim:\n{json.dumps(dossier_slim, ensure_ascii=False)[:2200]}\n"
        f"Prior deterministic findings:\n{json.dumps(prior_findings[:12], ensure_ascii=False)[:1500]}\n"
        f"Guide HTML excerpt (ambient stripped):\n{review_html[:4500]}\n"
    )


def build_external_review_report(
    context: dict[str, Any],
    *,
    llm_complete: LlmComplete | None = None,
) -> dict[str, Any]:
    """Build aulos.external_review/v1 as expert hard-flaw review → revise input."""
    html = str(
        (context.get("generation_rounds") or {}).get("draft_v1", {}).get("guide_html")
        or context.get("guide_html")
        or ""
    )
    dossier = dict(context.get("corpus_dossier") or {})
    work_title = str(context.get("work_title") or dossier.get("work_title") or "")
    composer = str(
        context.get("composer")
        or context.get("composer_guess")
        or dossier.get("composer")
        or ""
    )
    findings = _findings_from_hygiene(
        dossier,
        composer=composer,
        work_title=work_title,
        raw_message=str(context.get("raw_message") or ""),
        html=html,
    )
    findings.extend(
        _expert_hard_flaw_findings(
            work_title=work_title, composer=composer, html=html, dossier=dossier
        )
    )

    # Richness signal — used to distrust empty-body LLM hallucinations
    inv = _chamber_inventory(dossier)
    thesis_chars = int((inv.get("listening_thesis") or {}).get("chars") or 0)
    map_n = int((inv.get("listening_map") or {}).get("n") or 0)
    width_n = int((inv.get("width_points") or {}).get("n") or 0)
    dossier_rich = thesis_chars >= 40 or map_n >= 2 or width_n >= 2

    layer = "expert_deterministic"
    llm_blob = ""
    if llm_complete is not None:
        prompt = _expert_llm_prompt(
            work_title=work_title,
            composer=composer,
            html=html,
            dossier=dossier,
            prior_findings=findings,
        )
        try:
            llm_blob = llm_complete(prompt) or ""
        except Exception:  # noqa: BLE001
            llm_blob = ""
        if llm_blob:
            layer = "expert_llm"
            data = _parse_json_obj(llm_blob)
            if data:
                for f in data.get("findings") or []:
                    if not isinstance(f, dict) or not f.get("note"):
                        continue
                    code = str(f.get("code") or "expert_finding")
                    # Drop legacy source-hunt noise if the model still emits it
                    if code.startswith("web_") or "source" in code.lower():
                        continue
                    note = str(f.get("note"))
                    if any(x in note.lower() for x in ("web source", "信息源", "网页未", "sources under")):
                        continue
                    # Distrust empty-body claims when dossier already has craft chambers
                    empty_codes = {
                        "missing_guide_content",
                        "empty_body",
                        "only_ambient",
                        "no_guide_text",
                    }
                    if dossier_rich and (
                        code.lower() in empty_codes
                        or any(
                            x in note.lower()
                            for x in (
                                "only ambient",
                                "no text",
                                "缺少正文",
                                "只有 ambient",
                                "empty guide",
                                "无导赏",
                            )
                        )
                    ):
                        continue
                    findings.append(
                        {
                            "severity": str(f.get("severity") or "medium"),
                            "code": code,
                            "note": note,
                            "evidence": str(f.get("evidence") or "expert"),
                            "kind": "hard_flaw",
                        }
                    )
                for c in data.get("required_corrections") or []:
                    note = str(c or "").strip()
                    if not note:
                        continue
                    if any(x in note.lower() for x in ("web source", "信息源不足", "搜集来源")):
                        continue
                    if dossier_rich and any(
                        x in note.lower()
                        for x in ("only ambient", "缺少正文", "无导赏正文", "empty guide")
                    ):
                        continue
                    if note not in [x.get("note") for x in findings]:
                        findings.append(
                            {
                                "severity": "high",
                                "code": "expert_correction",
                                "note": note,
                                "evidence": "expert",
                                "kind": "hard_flaw",
                            }
                        )
                llm_verdict = str(data.get("verdict") or "").upper()
            else:
                llm_verdict = ""
        else:
            llm_verdict = ""
    else:
        llm_verdict = ""

    high = [f for f in findings if f.get("severity") == "high"]
    medium = [f for f in findings if f.get("severity") == "medium"]
    if high:
        verdict = "FAIL" if len(high) >= 2 else "REVISE"
    elif medium:
        verdict = "REVISE"
    elif llm_verdict in {"FAIL", "REVISE"}:
        verdict = llm_verdict
    else:
        verdict = "PASS"

    corrections: list[str] = []
    for f in findings:
        if f.get("severity") in {"high", "medium"}:
            note = str(f.get("note") or "")
            if note and note not in corrections:
                corrections.append(note)
    if verdict != "PASS" and not corrections:
        corrections.append(
            "按 IntentLock 重写导赏：去掉窜入作品/错误肖像，补齐聆听地图与作品解剖硬伤。"
        )

    hard_n = sum(1 for f in findings if f.get("kind") == "hard_flaw" or f.get("severity") == "high")
    summary = (
        f"专家视角（音乐导赏+音乐分析）{verdict}：硬伤/缺陷 {hard_n} 条，"
        f"共 {len(findings)} 条发现，layer={layer}。"
    )
    return {
        "schema": SCHEMA,
        "perspective": PERSPECTIVE,
        "verdict": verdict,
        "summary": summary,
        "findings": findings[:40],
        "required_corrections": corrections[:12],
        # Retained for schema compat; expert review does not hunt sources.
        "sources_used": [],
        "identity_check": {
            "ok": not any(
                f.get("code")
                in {
                    "portrait_composer_mismatch",
                    "foreign_family_dossier",
                    "html_title_drift",
                    "intent_betrayal",
                    "foreign_chamber_in_guide",
                    "h1_celebrity_pollution",
                    "rival_composer_dominance",
                    "form_title_mismatch",
                    "form_scale_mismatch",
                    "process_lock_in_product_prose",
                    "packaging_title_pollution",
                    "en_layer_cjk_pollution",
                }
                for f in findings
            ),
            "notes": [f.get("note") for f in high[:5]],
        },
        "layer": layer,
    }


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


def snapshot_draft(
    context: dict[str, Any],
    *,
    which: str,
    guide_html: str,
    summary: str = "",
    phase: str | None = None,
    findings: list[dict[str, str]] | None = None,
) -> None:
    """Persist draft_v1 / draft_v2 into generation_rounds with hard-flaw-aware scorecard."""
    from aulos_skills.revise_repair import score_draft_with_hard_flaws

    rounds = dict(context.get("generation_rounds") or {})
    rounds.setdefault("schema", ROUNDS_SCHEMA)
    # Never overwrite a frozen draft_v1
    if which == "draft_v1" and rounds.get("draft_v1", {}).get("guide_html"):
        context["generation_rounds"] = rounds
        return
    use_phase = phase or ("revise" if which == "draft_v2" else "compose")
    scorecard = score_draft_with_hard_flaws(
        html=guide_html,
        context=context,
        phase=use_phase,
        findings=findings,
    )
    entry = {
        "guide_html": guide_html,
        "summary": summary or str(context.get("summary") or ""),
        "process_scorecard": scorecard,
        "hard_flaws": list(scorecard.get("hard_flaws") or [])[:20],
    }
    rounds[which] = entry
    context["generation_rounds"] = rounds


def build_rounds_comparison(context: dict[str, Any]) -> dict[str, Any]:
    rounds = dict(context.get("generation_rounds") or {})
    v1 = dict(rounds.get("draft_v1") or {})
    v2 = dict(rounds.get("draft_v2") or {})
    r1 = (v1.get("process_scorecard") or {}).get("rollup") or {}
    r2 = (v2.get("process_scorecard") or {}).get("rollup") or {}
    p1 = float(r1.get("pct") or 0)
    p2 = float(r2.get("pct") or 0)
    flaws1 = int(r1.get("hard_flaws_remaining") or len(v1.get("hard_flaws") or []))
    flaws2 = int(r2.get("hard_flaws_remaining") or len(v2.get("hard_flaws") or []))
    if p2 > p1 + 0.5 or flaws2 < flaws1:
        winner = "v2"
    elif p1 > p2 + 0.5 and flaws1 <= flaws2:
        winner = "v1"
    else:
        winner = "tie"
    notes: list[str] = []
    report = dict(rounds.get("review_report") or context.get("external_review_report") or {})
    if report.get("verdict"):
        notes.append(f"Review verdict={report.get('verdict')}")
    if report.get("perspective"):
        notes.append(f"Perspective={report.get('perspective')}")
    notes.append(f"Score v1={p1:.1f}% → v2={p2:.1f}% (Δ {p2 - p1:+.1f})")
    notes.append(f"Hard flaws v1={flaws1} → v2={flaws2} (Δ {flaws2 - flaws1:+d})")
    repair_log = list(context.get("revise_repair_log") or [])
    if repair_log:
        notes.append("Repair: " + ", ".join(repair_log[:6]))
    comparison = {
        "v1_pct": p1,
        "v2_pct": p2,
        "delta_pct": round(p2 - p1, 1),
        "v1_hard_flaws": flaws1,
        "v2_hard_flaws": flaws2,
        "delta_hard_flaws": flaws2 - flaws1,
        "winner": winner,
        "notes": notes,
    }
    rounds["comparison"] = comparison
    rounds["schema"] = ROUNDS_SCHEMA
    if report:
        rounds["review_report"] = report
    context["generation_rounds"] = rounds
    return comparison
