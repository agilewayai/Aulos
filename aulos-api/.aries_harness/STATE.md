---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:90cd241a2cc4217d78e11651c3af6feb5c7e0f5e3a0e7fb56da1f8c3d0a8c151"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- STORY-002..005 auth MVP in progress

## Current phase (prior)

- Bootstrap STORY-001 in progress / ready for verify

## Active run

- RUN-BOOTSTRAP-001

## Hot facts

- Auth MVP foundation live: roles `user`/`superadmin`; Mailgun ops config; email verification required before login
- Live: https://aulos.purezen.ai (register/login) · https://aulos-ops.purezen.ai (superadmin)


- Project root: `aulos-api/`
- Role: API gateway
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent

## Open risks

- Cross-service contract drift between web, api, mcp, and agent
- Live upstream backends unverified in Sprint-0
