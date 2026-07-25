---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T10:55:22Z"
effective_status: "active"
effective_since: "2026-07-25T10:55:22Z"
content_fingerprint: "sha256:b6c5bb13b98787d2faf0fcb91ca5242e7a5a79fec1d887e74596a95d726897ab"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- Summarize complete for STORY-001 — ready for STORY-002 (live provider)

## Active run

- RUN-BOOTSTRAP-001 closed with VR-001

## Hot facts

- Project root: `aulos-agent/`
- Default LLM provider: `fake` (offline)
- Orchestration: hand-rolled LangGraph StateGraph (ADR-001)
- Offline verification: 7 pytest passed; CLI smoke passed

## Open risks

- langchain dependency version skew across providers
- live provider path unverified
