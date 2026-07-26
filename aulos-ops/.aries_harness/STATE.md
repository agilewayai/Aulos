---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:cbe474780dc47d63fa23d2ad9895994d66d7d6ba3ddf4df70eaa0ca4c6288ccc"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- STORY-PACK-002 daily Dev Blog shipped (verify/closeout)

## Active run

- RUN-DEV-BLOG-001

## Hot facts

- Project root: `aulos-ops/`
- Role: admin and ops portal
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-skills, aulos-ops
- Dev Blog tab → `/v1/ops/dev-blog*` (REQ-002 / SPEC-002)

## Open risks

- Live LLM prose quality depends on Ops provider config; fake path is offline-safe
- Host redeploy needed before live Ops shows the new tab
