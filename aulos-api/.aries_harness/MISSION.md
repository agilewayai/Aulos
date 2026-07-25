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
content_fingerprint: "sha256:63a3d7e6a447ba0a942a9af16d3e0b08d03f0d8b702f56830b36a0be833a0209"
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

## Success test

- pytest green; `/health` and `/v1/chat` work in fake mode; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
