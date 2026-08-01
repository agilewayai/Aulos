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
content_fingerprint: "sha256:15f62b4a031a5b7b8b11fcfb3fb933c6e5c53f0d4bac52e3fd46f8af4eb3ceba"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- Knowledge console modules shipped (Explore / Benchmark / Improve / Report / Composer dossier)

## Active run

- RUN-KNOWLEDGE-CONSOLE-010 (closing)

## Hot facts

- Project root: `aulos-ops/`
- Role: admin and ops portal
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-skills, aulos-ops
- Dev Blog tab → `/v1/ops/dev-blog*` (REQ-002 / SPEC-002)
- Knowledge plane modules under Knowledge console (SPEC-010)

## Open risks

- Live LLM prose quality depends on Ops provider config; fake path is offline-safe
- Host redeploy needed before live Ops shows the new tab
