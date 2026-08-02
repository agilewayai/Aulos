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
content_fingerprint: "sha256:e9b344ed71d299f399e510346f3092502891fd7766710f0317741bf4e63ff136"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- Knowledge console modules shipped and redeployed (Explore / Benchmark /
  Improve / Report / Composer dossier); Ops build `20260802071835-5476efb`
  served in production

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
- Browser-level visual smoke of the refreshed Ops build remains pending
