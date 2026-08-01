"""Token-boundary text match helpers (SPEC-032) — no per-work branches."""

from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def alias_in_text(alias: str, blob: str) -> bool:
    """True when alias appears as a whole token/phrase, not a substring of a longer word.

    Prevents performer surnames like ``Eschenbach`` from unlocking alias ``bach``.
    CJK aliases keep substring match (no alphabetic word boundaries).
    """
    a = (alias or "").strip().lower()
    if len(a) < 2:
        return False
    b = (blob or "").lower()
    if not b:
        return False
    if _CJK_RE.search(a):
        return a in b
    escaped = re.escape(a)
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", b) is not None


def numeric_token_in_text(token: str, blob: str) -> bool:
    """Digit-only tokens must not match inside longer digit runs (e.g. release ids)."""
    t = (token or "").strip().lower()
    if not t:
        return False
    b = (blob or "").lower()
    if t.isdigit():
        return re.search(rf"(?<!\d){re.escape(t)}(?!\d)", b) is not None
    return alias_in_text(t, blob)


def composers_compatible(a: str, b: str) -> bool:
    """Loose equality for IntentLock vs card/dossier composer strings."""
    x = re.sub(r"\s+", " ", (a or "").strip().lower())
    y = re.sub(r"\s+", " ", (b or "").strip().lower())
    if not x or not y:
        return False
    if x == y:
        return True
    # Last-name token overlap for "Wolfgang Amadeus Mozart" vs "Mozart"
    xt = {t for t in re.findall(r"[a-z\u4e00-\u9fff]{3,}", x)}
    yt = {t for t in re.findall(r"[a-z\u4e00-\u9fff]{3,}", y)}
    return bool(xt & yt)
