"""Recursive / iterative program deepen for multi-work Discogs pressings (SPEC-034Δ).

Not a single linear synthesize pass: for each program work, run a deepen iteration
(web evidence + LLM dossier + archetype floor), then fold results into the shelf.
"""

from __future__ import annotations

import re
from typing import Any

from aulos_skills.release_structure import (
    canonical_discogs_title,
    catalog_display,
    coerce_structure,
    is_multi_work_program,
    program_search_query,
    structure_from_context,
)
from aulos_skills.salon_codex import empty_dossier, merge_dossiers, parse_llm_dossier_json


_GENERIC_MAP_LABELS = {
    "orchestral thesis",
    "solo dialogue",
    "close",
    "opening",
    "middle",
    "乐队命题",
    "独奏对话",
    "收束",
}

_JUNK_HIT_MARKERS = (
    "bachlava",
    "url source:",
    "markdown content:",
    "published time:",
)


def iter_program_works(
    structure: dict[str, Any] | None,
    *,
    composer: str = "",
    max_works: int = 6,
) -> list[dict[str, Any]]:
    """Ordered program works for the deepen loop (capped for latency)."""
    st = coerce_structure(structure)
    if not is_multi_work_program(st):
        return []
    out: list[dict[str, Any]] = []
    for p in st.get("program") or []:
        if not isinstance(p, dict):
            continue
        raw_title = str(p.get("title") or "").strip()
        if not raw_title:
            continue
        title = canonical_discogs_title(raw_title)
        cats = list(p.get("catalog_numbers") or [])
        composers = [str(c) for c in (p.get("composers") or []) if c]
        work_composer = composers[0] if composers else (
            composer or str((st.get("composers") or [""])[0] or "")
        )
        out.append(
            {
                "index": p.get("index", len(out)),
                "title": title,
                "raw_title": raw_title,
                "composer": work_composer,
                "composers": composers,
                "catalog_numbers": cats,
                "instruments_hint": list(p.get("instruments_hint") or []),
                "track_titles": list(p.get("track_titles") or [])[:8],
                "search_query": program_search_query(
                    composer=work_composer,
                    title=title,
                    catalog_numbers=cats,
                ),
            }
        )
        if len(out) >= max_works:
            break
    return out


def _hit_is_usable(hit: str, *, cats: list[str], title: str) -> bool:
    h = str(hit or "")
    low = h.lower()
    if not h.strip():
        return False
    if any(m in low for m in _JUNK_HIT_MARKERS):
        return False
    # Prefer hits that mention catalog or a distinctive title token
    cat_needles = [catalog_display(c).lower() for c in cats if c]
    cat_needles += [str(c).lower() for c in cats if c]
    if cat_needles and any(n and n in low for n in cat_needles):
        return True
    tokens = [t for t in title.lower().replace(",", " ").split() if len(t) >= 5]
    if tokens and sum(1 for t in tokens[:4] if t in low) >= 2:
        return True
    # Reject composer-bio only dumps
    if "johann sebastian bach" in low and "concerto" not in low and not cat_needles:
        return False
    return "concerto" in low or "sonata" in low or "symphony" in low


def _first_text(values: list[Any]) -> str:
    for val in values:
        if isinstance(val, list):
            nested = _first_text(list(val))
            if nested:
                return nested
            continue
        text = str(val or "").strip()
        if text:
            return text
    return ""


def _prose_text(value: Any) -> str:
    """Return reader prose; parse accidental JSON strings before fan-in."""
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, dict):
        return _first_text(
            [
                value.get("listening_thesis"),
                value.get("work_introduction"),
                value.get("summary"),
                value.get("note"),
                value.get("cue"),
            ]
        )
    if isinstance(value, (list, tuple)):
        bits = [_prose_text(v) for v in value]
        return " ".join(b for b in bits if b).strip()
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return ""
    if "{" in text and "}" in text and (
        '"listening_thesis"' in text or "'listening_thesis'" in text or '"work_title"' in text
    ):
        parsed = parse_llm_dossier_json(text)
        if parsed:
            return _prose_text(parsed)
        return ""
    return text


def _is_weak_prose(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return True
    if len(low) < 36:
        return True
    return any(
        marker in low
        for marker in (
            "gathered from open sources",
            "web extracts not llm-verified",
            "no specific information",
            "not found in the provided sources",
            "markdown content:",
            "url source:",
        )
    )


def _identity_floor_sentence(
    *,
    title: str,
    composer: str,
    catalog: str,
    hints: list[str],
) -> str:
    forces = ", ".join(hints[:4])
    subject = f"{composer} — {title}" if composer else title
    cat = f" ({catalog})" if catalog and catalog != "unnumbered" else ""
    if forces:
        return (
            f"Lock {subject}{cat} as its own {forces} work inside this pressing; "
            "hear its opening role-allocation before comparing it with the other program works."
        )[:320]
    return (
        f"Lock {subject}{cat} as its own program work before comparing the recorded shelf."
    )[:260]


def _structure_program_rows(structure: dict[str, Any] | None) -> list[dict[str, Any]]:
    st = coerce_structure(structure)
    out: list[dict[str, Any]] = []
    for p in st.get("program") or []:
        if isinstance(p, dict):
            out.append(dict(p))
    return out


def _program_row_for_iteration(
    it: dict[str, Any],
    program_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    idx = it.get("index")
    for row in program_rows:
        if row.get("index") == idx:
            return row
    title = canonical_discogs_title(str(it.get("title") or ""))
    for row in program_rows:
        if canonical_discogs_title(str(row.get("title") or "")) == title:
            return row
    return {}


def _iteration_composer(
    it: dict[str, Any],
    *,
    program_row: dict[str, Any] | None = None,
    fallback: str = "",
) -> str:
    llm = dict(it.get("llm_dossier") or {})
    web_d = dict(it.get("web_dossier") or {})
    row = dict(program_row or {})
    return _first_text(
        [
            it.get("composer"),
            it.get("composers"),
            llm.get("composer"),
            web_d.get("composer"),
            row.get("composers"),
            fallback,
        ]
    )


def _work_deepdive_from_iteration(it: dict[str, Any]) -> dict[str, Any]:
    title = canonical_discogs_title(str(it.get("title") or "Program work"))
    cats = [str(c) for c in (it.get("catalog_numbers") or []) if c]
    cat_label = ", ".join(catalog_display(c) for c in cats) if cats else "unnumbered"
    llm = dict(it.get("llm_dossier") or {})
    web_d = dict(it.get("web_dossier") or {})
    note_dossier = parse_llm_dossier_json(str(it.get("llm_note") or ""))
    thesis = str(
        _prose_text(llm.get("listening_thesis"))
        or _prose_text(web_d.get("listening_thesis"))
        or _prose_text(note_dossier)
        or _prose_text(it.get("llm_note"))
        or ""
    ).strip()
    form = str(_prose_text(llm.get("form")) or _prose_text(web_d.get("form")) or "").strip()
    hints = [str(h) for h in (it.get("instruments_hint") or []) if h]
    floor = _identity_floor_sentence(
        title=title,
        composer=_iteration_composer(it),
        catalog=cat_label,
        hints=hints,
    )
    if _is_weak_prose(thesis):
        thesis = floor
    ear: list[str] = []
    if thesis and not _is_weak_prose(thesis):
        ear.append(thesis[:220])
    elif thesis:
        # Raw-web floor thesis is weak — prefer concrete snippets below
        pass
    if form:
        ear.append(f"Form focus: {form[:160]}")
    for h in list(it.get("web_hits") or []):
        if _hit_is_usable(str(h), cats=cats, title=title):
            # Strip provider prefix noise for chamber prose
            cue = str(h)
            if "]: " in cue:
                cue = cue.split("]: ", 1)[-1]
            ear.append(cue[:220])
        if len(ear) >= 4:
            break
    for wp in list(web_d.get("width_points") or [])[:3]:
        if wp and _hit_is_usable(str(wp), cats=cats, title=title):
            ear.append(str(wp)[:220])
        if len(ear) >= 5:
            break
    if not ear:
        ear = [
            floor,
            f"Role allocation: {', '.join(hints) if hints else 'ensemble'}",
            "Close: what remembers the opening gesture?",
        ]
    short_label = cat_label if cats else title[:72]
    return {
        "title": title[:160],
        "composer": _iteration_composer(it),
        "label": short_label,
        "focus": f"Program deepen · {cat_label}",
        "ear_cues": ear[:6],
        "catalog": cat_label,
        "listening_thesis": thesis[:280] if thesis else floor,
        "form": form,
        "web_sources": int(it.get("web_source_count") or 0),
        "llm_source": str(it.get("llm_source") or ""),
    }


def _sheet_id(kind: str, index: int, title: str, catalog: str = "") -> str:
    seed = f"{catalog or title or kind}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", seed).strip("-")[:42]
    return f"{kind}-{index + 1}-{slug}" if kind == "work" else "synthesis"


def _sound_summary_from_sources(
    it: dict[str, Any],
    dive: dict[str, Any],
    *,
    hints: list[str],
) -> str:
    notes: list[str] = []
    for src in (dict(it.get("llm_dossier") or {}), dict(it.get("web_dossier") or {})):
        sound = src.get("sound_world")
        if not isinstance(sound, dict):
            continue
        for value in sound.values():
            if isinstance(value, list):
                text = ", ".join(str(x) for x in value if x)
            else:
                text = str(value or "")
            text = text.strip()
            if text and text not in notes:
                notes.append(text)
    if notes:
        return "; ".join(notes[:3])[:420]
    cue = _first_text([dive.get("ear_cues")])
    if cue:
        return cue[:300]
    if hints:
        return f"Program forces: {', '.join(hints[:8])}"
    return ""


def _sheet_map_from_dive(dive: dict[str, Any], it: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    thesis = str(dive.get("listening_thesis") or "").strip()
    if thesis and "gathered from open sources" not in thesis.lower():
        rows.append({"label": "Identity lock", "cue": thesis[:240]})
    for cue in list(dive.get("ear_cues") or [])[:4]:
        text = str(cue or "").strip()
        if text:
            rows.append({"label": str(dive.get("label") or it.get("title") or "Cue")[:96], "cue": text[:240]})
    if not rows:
        rows.append(
            {
                "label": str(dive.get("label") or it.get("title") or "Program work")[:96],
                "cue": "Lock this work's opening identity before comparing the shelf.",
            }
        )
    return rows[:5]


def build_program_parallel_plan(
    structure: dict[str, Any] | None,
    iterations: list[dict[str, Any]] | None,
    sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic fan-out/fan-in plan for future worker-safe execution."""
    st = coerce_structure(structure)
    program_rows = _structure_program_rows(st)
    by_index = {s.get("index"): s for s in sheets if s.get("kind") == "work"}
    fan_out: list[dict[str, Any]] = []
    its = [dict(x) for x in (iterations or []) if isinstance(x, dict)]
    if its:
        rows = its
    else:
        rows = program_rows
    for i, item in enumerate(rows):
        row = _program_row_for_iteration(item, program_rows) if its else dict(item)
        idx = item.get("index", row.get("index", i))
        try:
            idx_i = int(idx)
        except (TypeError, ValueError):
            idx_i = i
        title = canonical_discogs_title(str(item.get("title") or row.get("title") or "Program work"))
        cats = [str(c) for c in (item.get("catalog_numbers") or row.get("catalog_numbers") or []) if c]
        composer = _iteration_composer(item, program_row=row)
        sheet = by_index.get(idx_i) or {}
        fan_out.append(
            {
                "stage": "work_deepen",
                "index": idx_i,
                "title": title,
                "composer": composer,
                "catalog_numbers": cats,
                "search_query": program_search_query(
                    composer=composer,
                    title=title,
                    catalog_numbers=cats,
                ),
                "sheet_id": sheet.get("id") or _sheet_id("work", idx_i, title, ", ".join(cats)),
            }
        )
    return {
        "schema": "aulos.program_parallel_plan/v1",
        "mode": "fan_out_fan_in",
        "fan_out": fan_out,
        "fan_in": "synthesis_sheet",
        "join_inputs": ["program_iterations", "guide_sheets[kind=work]"],
        "max_parallelism": min(len(fan_out), 6) if fan_out else 0,
        "concurrency_owner": "gateway_or_agent_runtime",
    }


def build_program_guide_sheets(
    structure: dict[str, Any] | None,
    iterations: list[dict[str, Any]] | None,
    dives: list[dict[str, Any]] | None,
    *,
    composer_names: list[str],
    catalog_label: str = "",
    listening_map: list[dict[str, Any]] | None = None,
    synthesis_summary: str = "",
    work_title: str = "",
    sound_world: dict[str, Any] | None = None,
    related_works: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """One work sheet per program identity plus one synthesis sheet."""
    st = coerce_structure(structure)
    if not is_multi_work_program(st):
        return []
    program_rows = _structure_program_rows(st)
    its = [dict(x) for x in (iterations or []) if isinstance(x, dict)]
    if not its:
        return []
    dive_rows = [dict(x) for x in (dives or []) if isinstance(x, dict)]
    sheets: list[dict[str, Any]] = []
    for i, it in enumerate(its):
        row = _program_row_for_iteration(it, program_rows)
        dive = dive_rows[i] if i < len(dive_rows) else _work_deepdive_from_iteration(it)
        idx = it.get("index", row.get("index", i))
        try:
            idx_i = int(idx)
        except (TypeError, ValueError):
            idx_i = i
        title = canonical_discogs_title(str(dive.get("title") or it.get("title") or row.get("title") or "Program work"))
        work_composer = str(dive.get("composer") or _iteration_composer(it, program_row=row)).strip()
        cats = [str(c) for c in (it.get("catalog_numbers") or row.get("catalog_numbers") or []) if c]
        cat_label = str(dive.get("catalog") or ", ".join(catalog_display(c) for c in cats) or "").strip()
        summary = str(dive.get("listening_thesis") or "").strip()
        if not summary or "gathered from open sources" in summary.lower():
            summary = _first_text(list(dive.get("ear_cues") or [])) or (
                f"Listen to {title} as its own locked work inside the program."
            )
        hints = [str(h) for h in (it.get("instruments_hint") or row.get("instruments_hint") or []) if h]
        sheets.append(
            {
                "id": _sheet_id("work", idx_i, title, cat_label),
                "kind": "work",
                "index": idx_i,
                "title": title,
                "composer": work_composer,
                "catalog": cat_label,
                "summary": summary[:360],
                "listening_map": _sheet_map_from_dive(dive, it),
                "deepdives": [
                    {
                        "title": title,
                        "focus": str(dive.get("focus") or f"Program work · {cat_label}")[:180],
                        "ear_cues": list(dive.get("ear_cues") or [])[:6],
                        "catalog": cat_label,
                    }
                ],
                "sound_world": _sound_summary_from_sources(it, dive, hints=hints),
                "source_count": int(it.get("web_source_count") or 0),
                "llm_source": str(it.get("llm_source") or ""),
            }
        )

    if len(sheets) < 2:
        return []
    names = [str(s.get("composer") or "").strip() for s in sheets if s.get("composer")]
    if not composer_names:
        composer_names = []
        for name in names:
            if name and name not in composer_names:
                composer_names.append(name)
    work_names = [
        f"{s.get('composer')} — {s.get('title')}" if s.get("composer") else str(s.get("title") or "")
        for s in sheets
    ]
    synthesis = {
        "id": "synthesis",
        "kind": "synthesis",
        "index": len(sheets),
        "title": "Program synthesis",
        "composer": " / ".join(composer_names[:8]),
        "catalog": catalog_label,
        "summary": (
            synthesis_summary
            or f"Hear {work_title or 'this pressing'} as a program of {len(sheets)} works: "
            + "; ".join(work_names[:6])
            + ". Compare the same recorded shelf only after each identity is stable."
        )[:700],
        "listening_map": list(listening_map or [])[:8],
        "deepdives": [
            {
                "title": "Synthesis route",
                "focus": "Program fan-in after per-work deepen",
                "ear_cues": [
                    "Name each work and catalog before comparing the recording.",
                    "Compare how the same forces change rhetoric across the shelf.",
                    "Keep pressing-level performer and label context separate from work identity.",
                ],
                "catalog": catalog_label,
            }
        ],
        "sound_world": dict(sound_world or {}),
        "related_works": list(related_works or [])[:12],
        "source_count": sum(int(s.get("source_count") or 0) for s in sheets),
        "llm_source": "synthesis_sheet",
    }
    return [*sheets, synthesis]


def fold_program_iterations(
    structure: dict[str, Any] | None,
    iterations: list[dict[str, Any]] | None,
    *,
    composer: str = "",
    work_title: str = "",
    performers: list[str] | None = None,
) -> dict[str, Any]:
    """Build shelf dossier patch from per-work deepen iterations."""
    from aulos_skills.release_structure import build_program_expand_dossier

    base = build_program_expand_dossier(
        structure or {},
        composer=composer,
        work_title=work_title,
        performers=performers,
    )
    if not base:
        return {}
    its = [dict(x) for x in (iterations or []) if isinstance(x, dict)]
    if not its:
        base["_provenance"] = {
            **dict(base.get("_provenance") or {}),
            "program_loop": "scaffold_only",
            "iterations": 0,
        }
        return base

    program_rows = _structure_program_rows(structure)
    dives = []
    for it in its:
        row = _program_row_for_iteration(it, program_rows)
        work_composer = _iteration_composer(it, program_row=row, fallback=composer)
        if work_composer and not it.get("composer"):
            it["composer"] = work_composer
        dive = _work_deepdive_from_iteration(it)
        if work_composer:
            dive["composer"] = work_composer
        dives.append(dive)

    composer_names: list[str] = []
    related: list[dict[str, Any]] = []
    subject_bits: list[str] = []
    thesis_bits: list[str] = []
    sound_notes: list[str] = []
    instrument_hints: list[str] = []
    catalogs_seen: list[str] = []
    for it, dive in zip(its, dives):
        title = str(dive.get("title") or it.get("title") or "Program work").strip()
        work_composer = str(dive.get("composer") or "").strip()
        if work_composer and work_composer not in composer_names:
            composer_names.append(work_composer)
        cats = [str(c) for c in (it.get("catalog_numbers") or []) if c]
        cat_label = ", ".join(catalog_display(c) for c in cats) if cats else str(dive.get("catalog") or "")
        for cat in cats:
            disp = catalog_display(cat)
            if disp and disp not in catalogs_seen:
                catalogs_seen.append(disp)
        subject_title = f"{work_composer} — {title}" if work_composer else title
        related.append(
            {
                "title": subject_title[:180],
                "relation": "Same Discogs pressing program",
                "catalog": cat_label,
            }
        )
        subject_bits.append(
            f"{subject_title}{f' ({cat_label})' if cat_label else ''}"
        )
        thesis = str(dive.get("listening_thesis") or "").strip()
        if thesis and "gathered from open sources" not in thesis.lower():
            thesis_bits.append(thesis)
        for hint in it.get("instruments_hint") or []:
            hint_s = str(hint or "").strip()
            if hint_s and hint_s not in instrument_hints:
                instrument_hints.append(hint_s)
        for dsrc in (dict(it.get("llm_dossier") or {}), dict(it.get("web_dossier") or {})):
            sw = dsrc.get("sound_world")
            if not isinstance(sw, dict):
                continue
            for val in sw.values():
                if isinstance(val, list):
                    text = ", ".join(str(x) for x in val if x)
                else:
                    text = str(val or "")
                text = text.strip()
                if text and text not in sound_notes:
                    sound_notes.append(text)

    listening_map = []
    for it, dive in zip(its, dives):
        if not it.get("title"):
            continue
        cue = str(dive.get("listening_thesis") or "").strip()
        if not cue or "gathered from open sources" in cue.lower():
            usable = [
                str(h)
                for h in (it.get("web_hits") or [])
                if _hit_is_usable(
                    str(h),
                    cats=list(it.get("catalog_numbers") or []),
                    title=str(it.get("title") or ""),
                )
            ]
            cue = (
                (usable[0].split("]: ", 1)[-1] if usable else "")
                or f"{dive.get('catalog')}: lock this work’s opening contract before comparing the shelf."
            )
        listening_map.append(
            {
                "label": str(dive.get("label") or dive.get("title") or "")[:96],
                "cue": cue[:240],
            }
        )
    depth_points = []
    width_points = list(base.get("width_points") or [])[:2]
    for it, dive in zip(its, dives):
        title = str(dive.get("title") or "")[:100]
        cats = str(dive.get("catalog") or "unnumbered")
        thesis = str(dive.get("listening_thesis") or "")
        if thesis and "gathered from open sources" not in thesis.lower():
            depth_points.append(f"{title} ({cats}): {thesis[:180]}")
        elif dive.get("ear_cues"):
            depth_points.append(f"{title} ({cats}): {str(dive['ear_cues'][0])[:180]}")
        else:
            depth_points.append(f"Deepen {title} ({cats}) with movement landmarks.")
        width_points.append(f"Program iteration: {title} [{cats}]")

    # Prefer iteration chambers over scaffold stubs
    base["variation_deepdives"] = dives
    if composer_names:
        base["composer"] = " / ".join(composer_names[:8])
    if catalogs_seen:
        base["catalog"] = " · ".join(catalogs_seen[:12])
    if subject_bits:
        base["listening_thesis"] = (
            f"Hear this pressing as {len(subject_bits)} locked program works: "
            + "; ".join(subject_bits[:6])
            + (". " + " ".join(thesis_bits[:3]) if thesis_bits else ".")
        )[:900]
        base["work_introduction"] = (
            f"{work_title or base.get('work_title') or 'This pressing'} is not a single anonymous work. "
            f"It is a program shelf of {len(subject_bits)} distinct works: "
            + "; ".join(subject_bits[:6])
            + ". The guide must deepen each identity before comparing the recording."
        )[:900]
        base["related_works"] = related[:12]
    if sound_notes or instrument_hints:
        base["sound_world"] = {
            "original_instrument": "Per program work; verify scoring at each catalog identity.",
            "ensemble_notes": "; ".join(sound_notes[:4])
            or f"Program forces: {', '.join(instrument_hints[:8])}",
            "modern_modes": ["Compare balance and articulation across program works"],
        }
    if listening_map:
        base["listening_map"] = listening_map
    if depth_points:
        base["depth_points"] = depth_points
    base["width_points"] = width_points[:12]
    guide_sheets = build_program_guide_sheets(
        structure,
        its,
        dives,
        composer_names=composer_names,
        catalog_label=str(base.get("catalog") or ""),
        listening_map=listening_map,
        synthesis_summary=str(base.get("listening_thesis") or ""),
        work_title=work_title or str(base.get("work_title") or ""),
        sound_world=dict(base.get("sound_world") or {}),
        related_works=related,
    )
    if guide_sheets:
        base["guide_sheets"] = guide_sheets
        base["program_parallel_plan"] = build_program_parallel_plan(structure, its, guide_sheets)
    zh = dict(base.get("zh") or {})
    zh["listening_map"] = [
        {
            "label": m["label"],
            "cue": m["cue"][:240],
        }
        for m in listening_map
    ]
    zh["variation_deepdives"] = [
        {
            "title": d["title"],
            "focus": d["focus"],
            "ear_cues": list(d.get("ear_cues") or [])[:4],
            "catalog": d.get("catalog"),
        }
        for d in dives
    ]
    zh["depth_points"] = [f"深化：{x}" for x in depth_points[:8]]
    if base.get("composer"):
        zh["composer"] = base["composer"]
    if subject_bits:
        zh["listening_thesis"] = (
            f"把这张唱片听成 {len(subject_bits)} 部已锁定身份的节目单："
            + "；".join(subject_bits[:6])
            + "。"
        )
        zh["work_introduction"] = (
            f"{work_title or base.get('work_title') or '本片'}不是匿名单一作品，"
            f"而是 {len(subject_bits)} 部作品的节目架构；先逐部深化，再比较录音。"
        )
    if guide_sheets:
        zh["guide_sheets"] = [
            {
                **s,
                "summary": (
                    f"这一页单独锁定 {s.get('composer') or ''}《{s.get('title') or ''}》；"
                    f"{s.get('summary') or ''}"
                    if s.get("kind") == "work"
                    else f"综合页：先逐部确认身份，再比较 {len(guide_sheets) - 1} 部作品在同一唱片中的关系。"
                )[:420],
            }
            for s in guide_sheets
        ]
    base["zh"] = zh
    base["zh_hans"] = dict(zh)
    base["raw_format"] = "release-program-loop"
    base["_provenance"] = {
        **dict(base.get("_provenance") or {}),
        "program_loop": "iterative",
        "iterations": len(its),
        "iteration_titles": [str(it.get("title") or "")[:80] for it in its],
    }
    return base


def strip_generic_family_map(dossier: dict[str, Any] | None) -> dict[str, Any]:
    """Remove family-scaffold map cues that drown program-specific landmarks."""
    d = dict(dossier or {})
    mp = []
    for row in d.get("listening_map") or []:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip().lower()
        if label in _GENERIC_MAP_LABELS:
            continue
        mp.append(row)
    if mp:
        d["listening_map"] = mp
    zh = dict(d.get("zh") or d.get("zh_hans") or {})
    if zh:
        zmap = []
        for row in zh.get("listening_map") or []:
            if not isinstance(row, dict):
                continue
            label = str(row.get("label") or "").strip().lower()
            if label in _GENERIC_MAP_LABELS:
                continue
            zmap.append(row)
        if zmap:
            zh["listening_map"] = zmap
            d["zh"] = zh
            d["zh_hans"] = dict(zh)
    return d


def apply_program_loop_to_context(context: dict[str, Any]) -> dict[str, Any]:
    """Synthesize-time: fold gateway program_iterations into corpus layers."""
    st = structure_from_context(context)
    iterations = list(context.get("program_iterations") or [])
    if not iterations and not is_multi_work_program(st):
        return context
    patch = fold_program_iterations(
        st,
        iterations,
        composer=str(context.get("composer") or context.get("composer_guess") or ""),
        work_title=str(context.get("work_title") or ""),
        performers=list((context.get("discogs") or {}).get("performers") or []),
    )
    if patch:
        context["program_loop_dossier"] = patch
        context["program_loop_applied"] = True
    return context


def merge_program_loop_layer(
    layers: list[dict[str, Any]],
    sources: list[str],
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    apply_program_loop_to_context(context)
    patch = dict(context.get("program_loop_dossier") or {})
    if not patch:
        return layers, sources
    layers = list(layers) + [patch]
    sources = list(sources) + ["release-program-loop"]
    return layers, sources


def finalize_program_dossier(merged: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """After merge_dossiers — prefer program loop chambers; drop generic family map."""
    out = dict(merged or {})
    patch = dict(context.get("program_loop_dossier") or {})
    if patch:
        # Force program-specific subject and chamber fields. Later album/family
        # layers must not re-generalize a structure-ready program loop.
        for key in (
            "composer",
            "catalog",
            "listening_thesis",
            "work_introduction",
            "form",
            "era",
            "sound_world",
            "related_works",
            "listening_map",
            "variation_deepdives",
            "width_points",
            "depth_points",
            "guide_sheets",
            "practice_notes",
            "myths_and_caveats",
        ):
            if patch.get(key):
                out[key] = patch[key]
        if patch.get("program_parallel_plan"):
            out["program_parallel_plan"] = patch["program_parallel_plan"]
        if patch.get("zh"):
            zh = dict(out.get("zh") or out.get("zh_hans") or {})
            zh.update({k: v for k, v in patch["zh"].items() if v not in (None, "", [], {})})
            out["zh"] = zh
            out["zh_hans"] = dict(zh)
        out["raw_format"] = patch.get("raw_format") or out.get("raw_format")
        prov = dict(out.get("_provenance") or {})
        prov.update(dict(patch.get("_provenance") or {}))
        out["_provenance"] = prov
    if context.get("program_expand_applied") or context.get("program_loop_applied"):
        out = strip_generic_family_map(out)
    return out
