"""Salon Codex email template craft tests."""

from __future__ import annotations

from aulos_api.services.email_templates import (
    ACCENT,
    STAGE,
    config_test_message,
    password_reset_message,
    render_salon_email,
    verification_message,
)


def test_render_salon_email_uses_concert_stage_tokens() -> None:
    html = render_salon_email(
        eyebrow="Aulos · Salon Codex",
        title="Hello salon",
        lede="A quiet invitation.",
        paragraphs=["Body line."],
        cta_label="Open",
        cta_url="https://aulos.purezen.ai/verify?token=abc",
        footnote="Ignore if unexpected.",
    )
    assert STAGE in html
    assert ACCENT in html
    assert "Fraunces" in html
    assert "Salon Codex" in html
    assert "https://aulos.purezen.ai/verify?token=abc" in html
    assert "Open" in html
    # no brochure clichés
    assert "#F4F1EA" not in html
    assert "purple" not in html.lower()


def test_verification_and_reset_messages_include_html() -> None:
    subj, text, html = verification_message(verify_url="https://example.com/verify?token=t1")
    assert "salon" in subj.lower() or "Verify" in subj
    assert "https://example.com/verify?token=t1" in text
    assert "Verify email" in html
    assert "Salon Codex" in html

    subj2, text2, html2 = password_reset_message(reset_url="https://example.com/?reset_token=r1")
    assert "password" in subj2.lower()
    assert "https://example.com/?reset_token=r1" in text2
    assert "Set new password" in html2
    assert STAGE in html2

    subj3, text3, html3 = config_test_message()
    assert "probe" in subj3.lower() or "Mail" in subj3 or "salon" in subj3.lower()
    assert "Mailgun" in text3 or "Ops" in text3
    assert "Salon Codex" in html3
