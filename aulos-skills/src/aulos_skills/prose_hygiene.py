"""Product-prose hygiene — strip process leaks; normalize packaging titles; language layers.

Systemic guards for Discogs/cold-path guides (SPEC-009 / SPEC-022 follow-on).
"""

from __future__ import annotations

import re
from typing import Any

_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_PROCESS_LOCK_RE = re.compile(
    r"(?i)^\s*(CRITIQUE\s*LOCK|REVIEW\s*REPAIR|REVIEW\s*:)\s*:?\s*"
)
_PROCESS_INLINE_RE = re.compile(
    r"(?i)\b(CRITIQUE\s*LOCK|REVIEW\s*REPAIR)\s*:\s*"
)

# Discogs / packaging noise that must not become IntentLock work titles.
_PACKAGING_TRAILING = re.compile(
    r"(?i)\s*[\[(/]?\s*("
    r"gesamtaufnahme|complete\s+recording|complete\s+edition|"
    r"vollst[aä]ndige?\s+aufnahme|intégrale|integrale|"
    r"box\s*set|digital\s+remaster(?:ed)?|remaster(?:ed)?|"
    r"original\s+jacket|anniversary\s+edition"
    r")\s*[\])/]?\s*$"
)
_MULTI_EQ_SPLIT = re.compile(r"\s*=\s*")
_SLASH_LANG_DUMP = re.compile(
    r"(?i)(lieder\s+ohne\s+worte|songs?\s+without\s+words|"
    r"romances?\s+sans\s+paroles|ges[aä]nge?\s+ohne\s+worte)"
)
_TRUNC_TAIL = re.compile(r"(?i)\s*/\s*(ges|rom|song|lied)\s*$")

# Form-cycle packaging canons (dimensional form names — not Catalog work_ids).
_FORM_CYCLE_CANON: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("songs without words", "lieder ohne worte", "gesange ohne worte", "gesänge ohne worte"),
        "Lieder ohne Worte (Songs Without Words)",
    ),
    (
        ("romances sans paroles",),
        "Romances sans paroles (Songs Without Words)",
    ),
)

def is_mostly_cjk(text: str, *, min_chars: int = 12) -> bool:
    s = (text or "").strip()
    if len(s) < min_chars:
        return bool(_CJK_RE.search(s)) and len(_CJK_RE.findall(s)) >= max(3, len(s) // 4)
    cjk = len(_CJK_RE.findall(s))
    return cjk >= max(8, int(0.35 * len(s)))


def strip_process_locks(text: str) -> str:
    """Remove CRITIQUE LOCK / REVIEW REPAIR prefixes and inline process tags from product prose."""
    out = (text or "").strip()
    if not out:
        return ""
    # Repeated lock prefixes
    for _ in range(4):
        nxt = _PROCESS_LOCK_RE.sub("", out).strip(" —;-|")
        if nxt == out:
            break
        out = nxt
    # If lock was glued with " — " keep the human thesis after last lock chunk
    if "CRITIQUE LOCK" in out.upper() or "REVIEW REPAIR" in out.upper():
        parts = re.split(r"(?i)\b(?:CRITIQUE\s*LOCK|REVIEW\s*REPAIR)\s*:\s*", out)
        # Prefer the last non-empty segment that looks like real prose
        for part in reversed(parts):
            cand = part.strip(" —;-|")
            if cand and not cand.lower().startswith("richness_empty"):
                # Drop leading correction-list junk before an em dash thesis
                if " — " in cand:
                    left, right = cand.split(" — ", 1)
                    if is_mostly_cjk(right) or len(right) > 40:
                        cand = right.strip()
                    elif not is_mostly_cjk(left) and len(left) < 80:
                        cand = right.strip() or left
                out = cand
                break
        else:
            # All parts were correction codes — take text after last em dash if any
            if " — " in out:
                out = out.rsplit(" — ", 1)[-1].strip()
    # Correction-code prefix without lock label: "richness_empty; missing_x — Thesis"
    if re.match(r"(?i)^(richness_empty|missing_\w+|intent_\w+|foreign_\w+)", out):
        if " — " in out:
            out = out.rsplit(" — ", 1)[-1].strip()
        else:
            out = re.sub(
                r"(?i)^(richness_empty|missing_\w+|intent_\w+|foreign_\w+)([;\s,]+[a-z0-9_]+)*\s*",
                "",
                out,
            ).strip(" —;-|")
    out = _PROCESS_INLINE_RE.sub("", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" —;-|")
    return out


def clean_packaging_work_title(raw: str, *, composer: str = "") -> str:
    """Turn Discogs release packaging titles into a listening-work title."""
    title = (raw or "").strip()
    if not title:
        return ""
    comp = (composer or "").strip()
    # Catalog / IntentLock canonical "Composer — Work" must stay intact (SPEC-032).
    # Aggressive surname peeling would otherwise turn Beethoven/Mozart shelves into
    # composer-less fragments ("Cello Sonatas…", "Symphony No. 40").
    if comp and title.lower().startswith(comp.lower()):
        after = title[len(comp) :]
        if re.match(r"^\s*[—–]\s+\S", after):
            return title[:160]
    # Drop leading composer-name bleed (surname / hyphenated compound only).
    # Do NOT allow a space+word swallow — that ate form nouns ("Mozart Symphony" → "No. 40").
    if comp:
        parts = [p for p in re.split(r"[\s\-]+", comp) if len(p) >= 4]
        for part in sorted(parts, key=len, reverse=True):
            title = re.sub(
                rf"(?i)^{re.escape(part)}(?:-[A-Za-z]+)?\s+",
                "",
                title,
            ).strip()
    # Prefer known form-cycle names if present in multi-language dump
    m = _SLASH_LANG_DUMP.search(title)
    if m and ("=" in title or title.count("/") >= 1):
        low = title.lower()
        for aliases, canon in _FORM_CYCLE_CANON:
            if any(a in low for a in aliases):
                title = canon
                break
        else:
            title = m.group(0).strip()
    else:
        # Take first segment before = packaging translations
        if "=" in title:
            parts = [p.strip() for p in _MULTI_EQ_SPLIT.split(title) if p.strip()]
            preferred = None
            for p in parts:
                if _SLASH_LANG_DUMP.search(p):
                    preferred = p
                    break
            title = preferred or parts[0]
        title = _PACKAGING_TRAILING.sub("", title).strip(" -–—/")
        title = _TRUNC_TAIL.sub("", title).strip(" -–—/")
        # Collapse remaining slash language pairs to primary
        if title.count("/") >= 2:
            primary = title.split("/")[0].strip()
            if len(primary) >= 8:
                title = primary
    # Composer duplication in title (space-separated, not Catalog em-dash form)
    if comp and title.lower().startswith(comp.lower()):
        rest = title[len(comp) :].lstrip(" -–—:").strip()
        if re.match(r"^[—–]", title[len(comp) :].lstrip() or ""):
            pass
        elif rest:
            title = rest
    # Strip leftover leading surname + separator — keep "Surname — Work" shapes.
    if comp:
        last = comp.split()[-1]
        if len(last) >= 4:
            if not re.match(rf"(?i)^{re.escape(last)}\s*[—–]\s+\S", title):
                title = re.sub(
                    rf"(?i)^{re.escape(last)}(?:-[A-Za-z]+)?\s*[-–—:]\s*",
                    "",
                    title,
                ).strip()
    return title[:160] or (raw or "")[:160]


def looks_like_packaging_dump(text: str) -> bool:
    """True when a bullet looks like Discogs multi-language packaging, not craft prose."""
    s = (text or "").strip()
    if not s:
        return False
    low = s.lower()
    if "from prior research cache:" in low and ("=" in s or "gesamtaufnahme" in low):
        return True
    if s.count("=") >= 2 and s.count("/") >= 1:
        return True
    if "gesamtaufnahme" in low or "complete recording" in low and "=" in s:
        return True
    if re.search(r"(?i)/\s*(ges|rom)\s*$", s):
        return True
    return False


def scrub_packaging_list_items(items: list[Any] | None) -> list[Any]:
    out: list[Any] = []
    for item in items or []:
        if isinstance(item, str) and looks_like_packaging_dump(item):
            continue
        out.append(item)
    return out


def scrub_dossier_process_locks(dossier: dict[str, Any]) -> dict[str, Any]:
    """Strip process locks from thesis/introduction and nested zh layers."""
    out = dict(dossier or {})
    for key in ("listening_thesis", "work_introduction", "work_title"):
        if isinstance(out.get(key), str):
            if key == "work_title":
                out[key] = clean_packaging_work_title(out[key], composer=str(out.get("composer") or ""))
            else:
                out[key] = strip_process_locks(out[key])
    for layer_key in ("zh", "zh_hans", "zh_hant"):
        layer = out.get(layer_key)
        if isinstance(layer, dict):
            cleaned = dict(layer)
            for key in ("listening_thesis", "work_introduction", "work_title"):
                if isinstance(cleaned.get(key), str):
                    if key == "work_title":
                        cleaned[key] = clean_packaging_work_title(
                            cleaned[key], composer=str(out.get("composer") or cleaned.get("composer") or "")
                        )
                    else:
                        cleaned[key] = strip_process_locks(cleaned[key])
            out[layer_key] = cleaned
    # myths may contain critique lines — keep as caveats but drop process prefixes
    myths = out.get("myths_and_caveats")
    if isinstance(myths, list):
        out["myths_and_caveats"] = [
            strip_process_locks(str(x)) if isinstance(x, str) else x for x in myths
        ]
    # Drop packaging-dump bullets from craft lists
    for key in ("width_points", "depth_points", "practice_notes", "related_works"):
        if isinstance(out.get(key), list):
            out[key] = scrub_packaging_list_items(out[key])
    return out


def partition_dossier_languages(dossier: dict[str, Any]) -> dict[str, Any]:
    """If EN-layer thesis is mostly CJK, move it into zh and clear EN for scaffold fill."""
    out = scrub_dossier_process_locks(dossier)
    thesis = str(out.get("listening_thesis") or "")
    intro = str(out.get("work_introduction") or "")
    zh = dict(out.get("zh") or out.get("zh_hans") or {})
    moved = False
    if thesis and is_mostly_cjk(thesis):
        if not str(zh.get("listening_thesis") or "").strip():
            zh["listening_thesis"] = thesis
        out["listening_thesis"] = ""
        moved = True
    if intro and is_mostly_cjk(intro):
        if not str(zh.get("work_introduction") or "").strip():
            zh["work_introduction"] = intro
        out["work_introduction"] = ""
        moved = True
    if moved:
        # Mirror list chambers into zh when zh lacks them
        for key in ("width_points", "depth_points", "listening_map", "myths_and_caveats", "practice_notes"):
            if out.get(key) and not zh.get(key):
                zh[key] = out.get(key)
        out["zh"] = zh
        out["zh_hans"] = zh
    return out


def infer_form_label(*, work_title: str, form: str = "", facets: dict[str, Any] | None = None) -> str:
    """Avoid bogus 'Large-scale work' placeholder for miniature / cycle shelves."""
    current = (form or "").strip()
    if current and "large-scale" not in current.lower() and "clarified in deep" not in current.lower():
        return current
    blob = f"{work_title} {current} {' '.join(str(x) for x in ((facets or {}).get('forms') or []))}".lower()
    rules = (
        (("songs without words", "lieder ohne worte", "romances sans paroles", "无词歌", "无言歌"),
         "Lyric piano miniatures (Songs Without Words / Lieder ohne Worte cycle)"),
        (("nocturne", "夜曲"), "Nocturne — lyric piano miniature"),
        (("mazurka", "玛祖卡"), "Mazurka — piano character dance"),
        (("prelude", "前奏曲"), "Prelude set / lyric piano miniature"),
        (("etude", "étude", "练习曲"), "Étude — piano study with concert life"),
        (("intermezzo",), "Intermezzo — short character piece"),
        (("cello suite", "unaccompanied cello", "无伴奏大提琴"), "Solo cello suite cycle"),
        (("goldberg", "variation"), "Variation cycle"),
        (("concerto", "协奏曲"), "Concerto"),
        (("symphony", "交响曲"), "Symphony"),
        (("sonata", "奏鸣曲"), "Sonata"),
        (("quartet", "四重奏"), "String quartet"),
    )
    for tokens, label in rules:
        if any(t in blob for t in tokens):
            return label
    return current or "Chamber / concert work — form follows the locked title"


def strip_ambient_from_html(html: str) -> str:
    """Remove ambient player chrome so expert review does not mistake it for empty body."""
    out = html or ""
    out = re.sub(
        r"<aside\b[^>]*class=[\"'][^\"']*ambient[^\"']*[\"'][^>]*>[\s\S]*?</aside>",
        "",
        out,
        flags=re.I,
    )
    out = re.sub(
        r"<script\b[^>]*id=[\"']aulos-ambient[^\"']*[\"'][^>]*>[\s\S]*?</script>",
        "",
        out,
        flags=re.I,
    )
    return out
