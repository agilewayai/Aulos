"""Salon Codex (沙龙典藏) email layouts — concert-stage Aulos visual language.

Tokens mirror listening-guide craft: dark stage, parchment accent, serif display.
HTML is table-based for mail-client safety; plain text is always provided as fallback.
"""

from __future__ import annotations

from html import escape

# Concert-stage palette (ARCH-003 / guide_render)
STAGE = "#0c1216"
PANEL = "#151c22"
INK = "#e8efe9"
MUTE = "#9aafa3"
ACCENT = "#c9a66b"
LINE = "rgba(232,239,233,0.14)"


def render_salon_email(
    *,
    eyebrow: str,
    title: str,
    lede: str,
    paragraphs: list[str],
    cta_label: str | None = None,
    cta_url: str | None = None,
    footnote: str | None = None,
    preheader: str | None = None,
) -> str:
    """Return a full HTML document in Salon Codex email style."""
    pre = escape(preheader or lede)[:140]
    eyebrow_e = escape(eyebrow)
    title_e = escape(title)
    lede_e = escape(lede)
    body_rows = "".join(
        f"""
              <tr>
                <td style="padding:0 0 14px 0;font-family:Manrope,'Segoe UI',Helvetica,Arial,sans-serif;font-size:15px;line-height:1.7;color:{MUTE};">
                  {escape(p)}
                </td>
              </tr>
        """
        for p in paragraphs
        if p.strip()
    )

    cta_block = ""
    if cta_label and cta_url:
        cta_block = f"""
              <tr>
                <td style="padding:10px 0 22px 0;">
                  <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                      <td style="background:{ACCENT};border-radius:2px;">
                        <a href="{escape(cta_url, quote=True)}"
                           style="display:inline-block;padding:14px 28px;font-family:Fraunces,Georgia,'Times New Roman',serif;font-size:15px;font-weight:700;letter-spacing:0.02em;color:{STAGE};text-decoration:none;">
                          {escape(cta_label)}
                        </a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:0 0 18px 0;font-family:Manrope,'Segoe UI',Helvetica,Arial,sans-serif;font-size:12px;line-height:1.55;color:{MUTE};word-break:break-all;">
                  Or open this link:<br/>
                  <a href="{escape(cta_url, quote=True)}" style="color:{ACCENT};text-decoration:underline;">{escape(cta_url)}</a>
                </td>
              </tr>
        """

    footnote_block = ""
    if footnote:
        footnote_block = f"""
              <tr>
                <td style="padding:18px 0 0 0;border-top:1px solid {LINE};font-family:Manrope,'Segoe UI',Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;color:{MUTE};">
                  {escape(footnote)}
                </td>
              </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <meta name="color-scheme" content="dark"/>
  <meta name="supported-color-schemes" content="dark"/>
  <title>{title_e}</title>
  <!--[if !mso]><!-->
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;600;700&display=swap" rel="stylesheet"/>
  <!--<![endif]-->
  <style>
    body {{ margin:0 !important; padding:0 !important; background:{STAGE}; }}
    a {{ color:{ACCENT}; }}
  </style>
</head>
<body style="margin:0;padding:0;background:{STAGE};">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    {pre}
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{STAGE};">
    <tr>
      <td align="center" style="padding:36px 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;background:{PANEL};border:1px solid {LINE};">
          <tr>
            <td style="height:3px;background:{ACCENT};font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:28px 28px 8px 28px;font-family:Manrope,'Segoe UI',Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:{ACCENT};">
              {eyebrow_e}
            </td>
          </tr>
          <tr>
            <td style="padding:4px 28px 12px 28px;font-family:Fraunces,Georgia,'Times New Roman',serif;font-size:28px;line-height:1.2;font-weight:700;letter-spacing:-0.02em;color:{INK};">
              {title_e}
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 20px 28px;font-family:Fraunces,Georgia,'Times New Roman',serif;font-size:16px;line-height:1.65;font-weight:500;color:{MUTE};">
              {lede_e}
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 8px 28px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="height:1px;background:{LINE};font-size:0;line-height:0;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 28px 8px 28px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                {body_rows}
                {cta_block}
                {footnote_block}
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 28px 28px;font-family:Manrope,'Segoe UI',Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;color:{MUTE};">
              Aulos · Salon Codex
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def verification_message(*, verify_url: str) -> tuple[str, str, str]:
    """Return (subject, text, html) for account verification."""
    subject = "Verify your Aulos salon invitation"
    text = (
        "Welcome to Aulos — your Salon Codex listening companion.\n\n"
        "Please verify your email to open the salon:\n"
        f"{verify_url}\n\n"
        "If you did not register, you may ignore this message.\n"
    )
    html = render_salon_email(
        eyebrow="Aulos · Salon Codex",
        title="Confirm your place in the salon",
        lede="A quiet invitation to deep listening — verify your email to begin composing guides.",
        paragraphs=[
            "Your account is almost ready. One confirmation keeps the salon private and trustworthy.",
            "After you verify, you can sign in and request listening guides shaped in the Salon Codex tradition.",
        ],
        cta_label="Verify email",
        cta_url=verify_url,
        footnote="If you did not create an Aulos account, you can safely ignore this letter.",
        preheader="Confirm your email to enter the Aulos salon.",
    )
    return subject, text, html


def password_reset_message(*, reset_url: str) -> tuple[str, str, str]:
    """Return (subject, text, html) for password reset."""
    subject = "Reset your Aulos salon password"
    text = (
        "We received a request to reset your Aulos password.\n\n"
        "Choose a new password here:\n"
        f"{reset_url}\n\n"
        "If you did not ask for a reset, you can ignore this message.\n"
    )
    html = render_salon_email(
        eyebrow="Aulos · Salon Codex",
        title="Restore access to your salon",
        lede="A one-time key to set a new password — calm, secure, and time-bound.",
        paragraphs=[
            "Someone requested a password reset for this email. Use the button below to choose a new password.",
            "The link expires after a limited time and can be used only once.",
        ],
        cta_label="Set new password",
        cta_url=reset_url,
        footnote="If you did not request this, ignore the letter — your password stays unchanged.",
        preheader="Set a new password for your Aulos account.",
    )
    return subject, text, html


def config_test_message() -> tuple[str, str, str]:
    """Return (subject, text, html) for Ops Mailgun probe."""
    subject = "Aulos salon — mail delivery probe"
    text = (
        "This is a test message from Aulos Ops.\n\n"
        "If you received it, Mailgun configuration is working.\n"
    )
    html = render_salon_email(
        eyebrow="Aulos Ops · Salon Codex",
        title="Mail delivery probe",
        lede="A quiet chime from the salon post — your Mailgun channel is speaking clearly.",
        paragraphs=[
            "This letter was sent from the Ops Mailgun configuration test.",
            "Receiving it means domain, API key, and from-address are aligned for live transactional mail.",
        ],
        footnote="No action is required. You may archive this note.",
        preheader="Mailgun configuration test from Aulos Ops.",
    )
    return subject, text, html
