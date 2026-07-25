---
schema_version: "0.1"
project_id: "aulos-api"
owner: "arthur"
doc_role: "verification-report"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:52:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:52:22Z"
content_fingerprint: "sha256:7f7f4a97e2023626d5f87b6ff400b032faf2153724f12ff1c32bff46010fe66d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# VR-002 — Auth MVP

## Checks
- pytest aulos-api: 7 passed (includes auth suite)
- Public register on https://aulos.purezen.ai/v1/auth/register
- Superadmin login + Mailgun GET/PUT on https://aulos-ops.purezen.ai
- Web/ops static builds succeeded and redeployed

## Residual
- Mail provider still `fake` until ops enables live Mailgun with real credentials
- Change bootstrap superadmin password in production via `.run/host.env`
