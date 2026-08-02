"""Soloist vs ensemble instrument evidence — SPEC-033 class gates.

Family packs that name a soloist (piano, violin, …) must not unlock from
ensemble/form tokens alone (orchestra + concerto ≠ piano-concerto).
"""

from __future__ import annotations

from typing import Any

# Token fragments / whole tokens treated as soloist-class evidence.
_SOLOIST_MARKERS: tuple[str, ...] = (
    "piano",
    "pianoforte",
    "fortepiano",
    "keyboard",
    "harpsichord",
    "钢琴",
    "鍵盤",
    "键盘",
    "羽管键琴",
    "violin",
    "violon",
    "viola",
    "cello",
    "violoncello",
    "小提琴",
    "中提琴",
    "大提琴",
    "oboe",
    "flute",
    "clarinet",
    "bassoon",
    "horn",
    "trumpet",
    "guitar",
    "organ",
    "双簧管",
    "长笛",
    "單簧管",
    "单簧管",
    "圆号",
    "小号",
    "吉他",
    "管风琴",
    "voice",
    "soprano",
    "tenor",
    "choir",
    "chorus",
    "合唱",
    "人声",
)

_ENSEMBLE_MARKERS: tuple[str, ...] = (
    "orchestra",
    "strings",
    "ensemble",
    "philharmonia",
    "philharmonic",
    "symphony orchestra",
    "管弦",
    "乐团",
    "樂隊",
    "乐队",
    "弦乐",
)


def is_soloist_token(token: str) -> bool:
    t = (token or "").lower().strip()
    if not t:
        return False
    if any(m in t for m in _ENSEMBLE_MARKERS):
        # "symphony orchestra" etc.
        if not any(s in t for s in _SOLOIST_MARKERS):
            return False
    return any(m in t for m in _SOLOIST_MARKERS)


def is_ensemble_token(token: str) -> bool:
    t = (token or "").lower().strip()
    return bool(t) and any(m in t for m in _ENSEMBLE_MARKERS)


def soloist_tokens(instruments: list[str]) -> list[str]:
    return [str(t).lower() for t in instruments if is_soloist_token(str(t))]


def token_hits_blob(token: str, blob: str) -> bool:
    t = (token or "").lower().strip()
    b = (blob or "").lower()
    if not t or not b:
        return False
    if t in b:
        return True
    # Peer aliases
    if t in {"cello", "violoncello", "大提琴"} and (
        "cello" in b or "violoncello" in b or "大提琴" in b
    ):
        return True
    if t in {"violin", "violon", "小提琴"} and (
        "violin" in b or "小提琴" in b
    ):
        return True
    if t in {"viola", "中提琴"} and ("viola" in b or "中提琴" in b):
        return True
    if t in {"piano", "pianoforte", "fortepiano", "钢琴", "鍵盤", "键盘"} and (
        "piano" in b or "钢琴" in b or "鍵盤" in b or "键盘" in b or "fortepiano" in b
    ):
        return True
    if t in {"oboe", "双簧管"} and ("oboe" in b or "双簧管" in b):
        return True
    return False


def family_soloist_tokens(family: dict[str, Any]) -> list[str]:
    match = dict(family.get("match") or {})
    instruments = [str(t) for t in (match.get("instruments") or []) if t]
    return soloist_tokens(instruments)


def family_requires_soloist_evidence(family: dict[str, Any]) -> bool:
    return bool(family_soloist_tokens(family))


def family_soloist_misses_blob(family: dict[str, Any], blob: str) -> bool:
    """True when family declares soloists and none hit the blob."""
    solo = family_soloist_tokens(family)
    if not solo:
        return False
    return not any(token_hits_blob(t, blob) for t in solo)


def blob_soloist_markers(blob: str) -> set[str]:
    """Coarse soloist classes present in a title/message blob."""
    b = (blob or "").lower()
    found: set[str] = set()
    checks: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("piano", ("piano", "fortepiano", "pianoforte", "钢琴", "鍵盤", "键盘")),
        ("violin", ("violin", "小提琴")),
        ("viola", ("viola", "中提琴")),
        ("cello", ("cello", "violoncello", "大提琴")),
        ("oboe", ("oboe", "双簧管")),
        ("flute", ("flute", "长笛")),
        ("clarinet", ("clarinet", "单簧管", "單簧管")),
        ("organ", ("organ", "管风琴")),
        ("guitar", ("guitar", "吉他")),
        ("voice", ("choir", "chorus", "requiem", "合唱", "弥撒", "安魂")),
    )
    for cls, needles in checks:
        if any(n in b for n in needles):
            found.add(cls)
    return found


def family_conflicts_blob_soloists(family: dict[str, Any], blob: str) -> bool:
    """True when blob names a soloist class the family does not claim.

    Example: violin+oboe title vs piano-concerto pack.
    """
    family_solo = {c for t in family_soloist_tokens(family) for c in blob_soloist_markers(t)}
    # Map family tokens to classes more directly
    for t in family_soloist_tokens(family):
        family_solo |= blob_soloist_markers(t)
    blob_solo = blob_soloist_markers(blob)
    if not family_solo or not blob_solo:
        return False
    # Foreign soloists present beyond what the family claims
    foreign = blob_solo - family_solo - {"voice"}
    # Voice often coexists; ignore. Ensemble-only blobs have empty blob_solo.
    return bool(foreign)


def product_solo_instrument_drift(
    *,
    title_blob: str,
    narrative_blob: str,
) -> bool:
    """True when locked title is non-piano solo scoring but narrative is piano-concerto rhetoric."""
    title_solo = blob_soloist_markers(title_blob)
    if "piano" in title_solo:
        return False
    if not (title_solo & {"violin", "viola", "cello", "oboe", "flute", "clarinet"}):
        return False
    narr = (narrative_blob or "").lower()
    piano_rhetoric = (
        "piano concerto" in narr
        or "钢琴协奏" in narr
        or "鋼琴協奏" in narr
        or "fortepiano" in narr
        or ("cadenza" in narr and "piano" in narr)
        or ("华彩" in narr and "钢琴" in narr)
    )
    return piano_rhetoric
