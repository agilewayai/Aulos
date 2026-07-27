"""Unit tests for guide HTML sanitizer (SPEC-015 / AUDIT-009 F2)."""

from __future__ import annotations

from aulos_api.services.guide_html_security import (
    prepare_public_guide_html,
    sanitize_guide_html,
)


def test_sanitize_strips_javascript_urls_and_event_handlers() -> None:
    raw = (
        '<html><body>'
        '<a href="javascript:alert(document.cookie)">click</a>'
        '<a href="https://example.com/safe">ok</a>'
        '<img src="x" onerror="fetch(\'/steal\')">'
        '<form action="vbscript:msgbox(1)"></form>'
        "</body></html>"
    )
    out = sanitize_guide_html(raw)
    assert "javascript:" not in out.lower()
    assert "vbscript:" not in out.lower()
    assert "onerror" not in out.lower()
    assert "https://example.com/safe" in out
    assert 'href="#"' in out


def test_prepare_public_guide_html_sanitizes_then_hardens() -> None:
    raw = (
        "<html><head></head><body>"
        '<a href="javascript:steal()">bad</a>'
        "<p>guide body</p>"
        "</body></html>"
    )
    out = prepare_public_guide_html(raw)
    assert "javascript:" not in out.lower()
    assert "aulos-mobile-harden" in out or "aulos-share-chrome" in out
