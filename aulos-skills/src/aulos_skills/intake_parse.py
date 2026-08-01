"""Generic listening-intent text parsing — no per-composer code branches.

Catalog aliases remain the authority for known names; heuristics only recover
clear title/composer shapes from the listener's sentence.
"""

from __future__ import annotations

import re
from typing import Any

# Listener chat chrome — strip before treating residue as a work title.
_BOILERPLATE_PATTERNS = (
    r"(?i)\b(i('m| am)?|listening to|learning|study|studying|help me|please|about|"
    r"the work|write|compose|create|make|a listening guide|listening guide)\b",
    r"我准备开始欣赏|准备开始欣赏|我想欣赏|我想听|请帮我|帮我写|帮我|"
    r"写一份|详细的?欣赏导赏|欣赏导赏|导赏|听赏|一份",
    r"[。．！!？?]",
)

# Studio slash command: /discogs #<release-id|catno>
# Examples: /discogs #4084139  |  /discogs 423-287-1  |  /discogs #423 287-1
_DISCOGS_CMD_RE = re.compile(
    r"(?i)(?:^|\s)/discogs\s+#?(?P<ref>"
    r"\d+(?:[\s\-–—./]+\d+[A-Za-z0-9]*)+"  # catalog-style (must have separator)
    r"|\d+"  # bare release / master id
    r")(?=\s|$|[^\w\-–—./])"
)


def parse_discogs_command(text: str) -> dict[str, str] | None:
    """Return release_id or catno when message contains /discogs …; else None."""
    m = _DISCOGS_CMD_RE.search(text or "")
    if not m:
        return None
    ref = re.sub(r"\s+", " ", (m.group("ref") or "").strip())
    if not ref:
        return None
    if re.search(r"[\s\-–—./]", ref):
        # Normalize common DG-style: 423-287-1 → keep; also expose spaced form later.
        return {"catno": ref, "command": "discogs", "ref_kind": "catno"}
    if ref.isdigit():
        return {"release_id": ref, "command": "discogs", "ref_kind": "release"}
    return None


# Back-compat alias (deprecated name)
parse_discog_command = parse_discogs_command

_BOOK_TITLE_RE = re.compile(r"[《〈]([^》〉]{1,80})[》〉]")
_CN_QUOTE_RE = re.compile(r"[「『]([^」』]{1,80})[」』]")
_LATIN_QUOTE_RE = re.compile(r"[\"“](.+?)[\"”]")
# 德沃夏克《杜姆卡》… / Dvořák — Dumky / Composer: Work
_CN_COMPOSER_BOOK_RE = re.compile(
    r"([\u4e00-\u9fff·•．.\-]{2,20})\s*[《〈]([^》〉]{1,80})[》〉]"
)
_EN_COMPOSER_DASH_RE = re.compile(
    # Require whitespace around ASCII "-" / ":" so hyphenated surnames
    # (Mendelssohn-Bartholdy) are never treated as composer/title separators.
    # Em/en dashes may still sit tight: "Mozart—Concerto".
    r"(?i)\b([A-ZÀ-ÖØ-Þ][\wÀ-öø-ÿ'.\-]+(?:\s+[A-ZÀ-ÖØ-Þ][\wÀ-öø-ÿ'.\-]+){0,3})"
    r"(?:\s*[—–]\s*|\s+[-:]\s+)([^\n]{2,160})"
)
_LEADING_PREPOSITIONS = re.compile(
    r"(?i)^(i('m| am)?\s+)?(listening\s+to\s+|to|by|of|for|on|about|with|from|the)\s+"
)
_PERFORMER_TAIL_RE = re.compile(
    r"(?i)\s+(performed by|featuring|with performers?)\b.+$"
)
# Diary / atelier structured lines (SPEC-021 message builder)
_STRUCTURED_COMPOSER_LINE = re.compile(r"(?im)^Composers?:\s*(.+)$")
_STRUCTURED_WORK_LINE = re.compile(
    r"(?im)^(?:Work|Title|listening guide.*?for)\s*[:=]\s*[\"“]?(.+?)[\"”]?\s*$"
)


def strip_listening_boilerplate(text: str) -> str:
    cleaned = text or ""
    for pat in _BOILERPLATE_PATTERNS:
        cleaned = re.sub(pat, " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,!?:;-、，的了呢吧啊呀")
    return cleaned


def extract_quoted_title(text: str) -> str | None:
    for regex in (_BOOK_TITLE_RE, _CN_QUOTE_RE, _LATIN_QUOTE_RE):
        m = regex.search(text or "")
        if m:
            title = m.group(1).strip(" .,!?:;-、，")
            if len(title) >= 1:
                return title
    return None


def _alias_usable(alias: str) -> bool:
    a = (alias or "").strip()
    if not a:
        return False
    if re.search(r"[\u4e00-\u9fff]", a):
        return len(a) >= 2
    return len(a) >= 3


def match_composer_from_catalog(text: str, composers: dict[str, Any]) -> tuple[str, str]:
    """Return (composer_id, display_name) from catalog aliases — longest alias wins."""
    from aulos_skills.text_match import alias_in_text

    blob = text or ""
    best: tuple[int, str, str] | None = None
    for card in composers.values():
        aliases = list(getattr(card, "aliases", None) or [])
        name_en = str(getattr(card, "name_en", "") or "")
        name_zh = str(getattr(card, "name_zh", "") or "")
        composer_id = str(getattr(card, "composer_id", "") or "")
        for alias in aliases + [name_en, name_zh]:
            if not _alias_usable(alias):
                continue
            needle = alias.lower()
            if alias_in_text(needle, blob):
                score = len(needle)
                display = name_en or name_zh or alias
                if best is None or score > best[0]:
                    best = (score, composer_id, display)
    if best:
        return best[1], best[2]
    return "", ""


def guess_composer_and_title(text: str, *, catalog_composers: dict[str, Any] | None = None) -> dict[str, str]:
    """Best-effort work_title + composer from free text (catalog first, then shapes)."""
    raw = text or ""
    composers = catalog_composers or {}

    composer_id, composer = match_composer_from_catalog(raw, composers)

    # Structured atelier/diary fields beat free-text heuristics when present.
    struct_composer = ""
    m_comp = _STRUCTURED_COMPOSER_LINE.search(raw)
    if m_comp:
        struct_composer = m_comp.group(1).split(",")[0].strip(" .,;:")
        if struct_composer and not composer:
            composer = struct_composer
            # Re-match catalog with the structured name alone for composer_id
            if composers and not composer_id:
                composer_id, catalog_name = match_composer_from_catalog(struct_composer, composers)
                if catalog_name:
                    composer = catalog_name

    book = _CN_COMPOSER_BOOK_RE.search(raw)
    quoted = extract_quoted_title(raw)
    en_dash = _EN_COMPOSER_DASH_RE.search(raw)

    work_title = ""
    if book:
        before = book.group(1).strip()
        title_core = book.group(2).strip()
        # Keep a short form/ensemble tail after the book title when present.
        tail = raw[book.end() :]
        tail = strip_listening_boilerplate(tail)
        tail = re.sub(r"^(的|之)", "", tail).strip(" .,!?:;-、，")
        # Keep only a short musical noun phrase (三重奏/奏鸣曲…)
        tail_m = re.match(r"^([\u4e00-\u9fffA-Za-z0-9\- ]{0,12})", tail)
        tail_bit = (tail_m.group(1) if tail_m else "").strip()
        work_title = f"{title_core}{tail_bit}" if tail_bit else title_core
        if not composer and len(before) >= 2:
            composer = before
    elif quoted:
        work_title = quoted
    elif en_dash:
        if not composer:
            composer = en_dash.group(1).strip()
        work_title = en_dash.group(2).strip(" .,!?:;-")
        work_title = strip_listening_boilerplate(work_title)

    # Prefer structured composer over dash-parse performer chrome ("Horowitz Plays Mozart…")
    if struct_composer:
        if composers:
            cid2, cname2 = match_composer_from_catalog(struct_composer, composers)
            if cname2:
                composer = cname2
                composer_id = cid2 or composer_id
            else:
                composer = struct_composer
        else:
            composer = struct_composer

    composer = _LEADING_PREPOSITIONS.sub("", (composer or "").strip()).strip(" .,!?:;-")
    if work_title:
        work_title = _PERFORMER_TAIL_RE.sub("", work_title).strip(" .,!?:;-")
        work_title = _LEADING_PREPOSITIONS.sub("", work_title).strip(" .,!?:;-")

    if not work_title:
        cleaned = strip_listening_boilerplate(raw)
        work_title = cleaned[:160] if len(cleaned) >= 2 else ""

    # If catalog matched a composer but title still embeds the name, tidy it.
    if composer and work_title:
        card = composers.get(composer_id) if composer_id else None
        names = [composer]
        if card is not None:
            names.extend(
                [
                    str(getattr(card, "name_en", "") or ""),
                    str(getattr(card, "name_zh", "") or ""),
                    *[str(a) for a in (getattr(card, "aliases", None) or [])],
                ]
            )
        # Longer aliases first (Mendelssohn-Bartholdy before Mendelssohn)
        names = sorted({n for n in names if n}, key=len, reverse=True)
        for name in names:
            if name and name in work_title and name != work_title:
                work_title = work_title.replace(name, " ").strip(" —–-·、， ")
                work_title = re.sub(r"\s+", " ", work_title)
        # Drop leftover hyphenated surname bleed (Bartholdy …) after partial strip
        try:
            from aulos_skills.prose_hygiene import clean_packaging_work_title

            work_title = clean_packaging_work_title(work_title, composer=composer)
        except Exception:  # noqa: BLE001
            work_title = re.sub(
                r"(?i)^(bartholdy|mendelssohn[- ]?bartholdy)\s+",
                "",
                work_title,
            ).strip(" —–-·、， ")

    return {
        "work_title": work_title,
        "composer": composer,
        "composer_id": composer_id,
    }
