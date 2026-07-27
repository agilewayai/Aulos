---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:55:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:55:00Z"
content_fingerprint: "sha256:943ea1afd6509c532e415b0bda0abb6a04fc8ffb3baa533e29d01965186de6a2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-010 — Salon Codex transactional email craft

## Document Control

- Spec ID: SPEC-010
- Title: Salon Codex email templates
- Status: active
- Related: SPEC-002 auth mail flows; ARCH-003 visual language

## Behaviors

1. All transactional mail (verify, password reset, Mailgun config probe) renders **HTML + plain text**.
2. HTML follows Salon Codex concert-stage tokens: stage `#0c1216`, parchment accent `#c9a66b`, Fraunces/Georgia display, Manrope/system body.
3. Layout: dark outer stage, bordered folio panel, gold hairline, eyebrow `Aulos · Salon Codex`, serif title, parchment CTA when a link applies.
4. Mailgun live send includes `html` field alongside `text`.
5. Fake mailbox stores `html` for offline inspection.

## Non-goals

- Marketing newsletters
- Per-locale template packs in this slice (English salon voice; Chinese UI remains separate)

## Acceptance

- `pytest tests/test_email_templates.py tests/test_mailgun.py tests/test_auth.py` green
