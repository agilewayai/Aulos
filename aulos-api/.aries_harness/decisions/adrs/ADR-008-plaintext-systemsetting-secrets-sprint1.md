---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T09:20:00Z"
effective_status: "active"
effective_since: "2026-07-27T09:20:00Z"
content_fingerprint: "sha256:3fda4058d935dd12519db919577c77268bcd0c3c05f94211915965b1d2fce368"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-008 — Plaintext provider secrets in SystemSetting (Sprint-1)

## Status

accepted (Sprint-1 risk; revisit before production hardening)

## Context

AUDIT-009 F11: Mailgun, LLM, Brave, Discogs, and embedding API keys/tokens are stored as plaintext JSON in `SystemSetting`. DB dumps and backup copies therefore expose third-party credentials.

## Decision

For Sprint-1 / hackathon deployment, **accept plaintext `SystemSetting` secrets** with compensating controls rather than shipping encryption-at-rest immediately.

## Compensating controls

1. Ops GET responses never echo secret values — only `*_set: true/false` flags.
2. Postgres/SQLite data directories and `.run/` are operator-private; not committed to git.
3. Host deploy requires non-default JWT / knowledge admin tokens in ignored `.run/host.env` (AUDIT-009 F1 code gate).
4. Superadmin role gates all settings mutation routes.
5. Audit logs and delivery rows must not persist raw API keys.

## Non-goals (deferred)

- Application-level encryption-at-rest with a KMS/master key
- Secret rotation UI beyond overwrite-on-save
- Hardware HSM

## Consequences

- Sprint-1 can ship without key-management infrastructure.
- Before claiming production signoff beyond hackathon scope, open a follow-up REQ for encrypted settings (Fernet/AES-GCM + `AULOS_SETTINGS_KEY`) and redacted backup procedures.
- This ADR closes AUDIT-009 F11 as **accepted risk with documented controls**.
