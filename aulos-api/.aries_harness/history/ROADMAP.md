---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "history-roadmap"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:43Z"
generated_at: "2026-07-27T10:25:06+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:06+00:00"
content_fingerprint: "sha256:67f4fb7c5947d53445cc65b214d09f779bec5f3fd8f2b044a29fc7ec158deca1"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Roadmap Snapshot

Generated at: `2026-07-27T10:25:06+00:00`

## Outcome target

- Deliver an HTTP API gateway (`aulos-api`) that fronts agent and MCP backends for the web GUI and other clients.

## Current milestone

- no current milestone recorded

## Now

- no next action recorded

## Next

- no next action recorded

## Later / guardrails

- In scope: FastAPI app, health + chat routes, fake-agent mode, CORS, offline pytest, harness artifact ladder
- Out of scope: auth/SSO, rate limiting productization, multi-tenant tenancy, production deploy
- pytest green; `/health` and `/v1/chat` work in fake mode; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
