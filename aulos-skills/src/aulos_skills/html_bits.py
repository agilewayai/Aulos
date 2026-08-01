"""Shared HTML/list text helpers — single coerce path for dossier points (META-001 §3.5)."""

from __future__ import annotations

from html import escape
from typing import Any


def point_text(item: Any) -> str:
    """Normalize width/depth/rag points that may arrive as str or single-key dict."""
    if item is None:
        return ""
    if isinstance(item, dict):
        parts: list[str] = []
        for k, v in item.items():
            key = str(k).strip()
            val = str(v).strip() if v is not None else ""
            if key and val:
                parts.append(f"{key}: {val}")
            elif val:
                parts.append(val)
            elif key:
                parts.append(key)
        return "; ".join(parts)
    return str(item).strip()


def point_texts(items: list[Any] | None, *, limit: int | None = None) -> list[str]:
    out: list[str] = []
    for item in items or []:
        text = point_text(item)
        if text:
            out.append(text)
        if limit is not None and len(out) >= limit:
            break
    return out


def html_li(items: list[Any], *, scrub: Any | None = None) -> str:
    """Build <li> list; optional scrub(text)->text (e.g. strip_tech_leaks_zh)."""
    out: list[str] = []
    for p in items or []:
        text = point_text(p)
        if scrub is not None and text:
            text = scrub(text) or ""
        if text:
            out.append(f"<li>{escape(text)}</li>")
    return "".join(out)


def html_p(text: str, *, scrub: Any | None = None) -> str:
    text = (text or "").strip()
    if scrub is not None and text:
        text = scrub(text) or ""
    return f"<p>{escape(text)}</p>" if text else ""
