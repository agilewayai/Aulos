---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T17:20:00Z"
effective_status: "active"
effective_since: "2026-07-26T17:20:00Z"
content_fingerprint: "sha256:947c69a12a93da56a1c917f28ac4b2b21c87f5088bb0c80553654cc2a275855f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-004 — Studio chain diagnostic log viewer

Upstream: API SPEC-012.

## Behavior

After a listening guide completes, studio loads `GET /v1/listening-guides/{id}/trace`
and shows a **Diagnostic log** disclosure under Chain of thought:

- deviation count / clean badge
- milestone list (`id`, `status`, `summary`)
- identity arc stages

## Acceptance

- Trace loads for completed guides; missing pre-SPEC-012 → no panel.
- Expand/collapse works without leaving studio.
