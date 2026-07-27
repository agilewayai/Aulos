---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:c10caeec7c4dc7a0d3a58bf6eb8158b2805d27850466e66ecced73dff9e6ad18"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- SPEC-008 session scene restore shipped (with asset auto-refresh)

## Active run

- idle


## Hot facts

- Project root: `aulos-web/`
- Role: web GUI
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent
- Auth: register / verify / login + forgot / reset (SPEC-002)
- Studio: **+** → Discogs search → compose via `/discogs #id`
- UX: auth gate + studio tabs + compose dock (SPEC-005)

## Open risks

- Live Mailgun required for real reset emails (fake mode offline-ok)
- Discogs rate limits without OPS token
