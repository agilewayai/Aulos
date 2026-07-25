---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "managed-doc"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:783fc130e724b2963889ecc2f772b1ed443542237630db37e35360894e8ce31a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Harness Design Memo

## Target frame

- `aulos-ops` (admin and ops portal) under aries-harness

## Base loop

- Inspect → Plan → Edit → Verify → Summarize

## Minimum artifacts

- MISSION, STATE, TASK_STACK, REQ/SPEC/STORY/ARCH/ADR, EC, REG, TRACE
