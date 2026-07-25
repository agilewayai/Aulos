---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:a9d1a1b9d22a061c809fbba1d030922a87fb16a08515115566aa28509b4ed55d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

## Outcome

- Deliver an HTTP API gateway (`aulos-api`) that fronts agent and MCP backends for the web GUI and other clients.

## Scope boundary

- In scope: FastAPI app, health + chat routes, fake-agent mode, CORS, offline pytest, harness artifact ladder
- Out of scope: auth/SSO, rate limiting productization, multi-tenant tenancy, production deploy

## Active MVP

- REQ-002 / SPEC-002: users-roles auth + Mailgun email validation + superadmin ops config

## Success test

- pytest green; `/health` and `/v1/chat` work in fake mode; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
