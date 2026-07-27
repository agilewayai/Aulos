---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T17:25:00+00:00"
generated_at: "2026-07-27T11:49:37+00:00"
effective_status: "generated"
effective_since: "2026-07-27T11:49:37+00:00"
content_fingerprint: "sha256:04ba811f44e95353247cb31fd6f53ff8300f1771bb139c22a8fa42f98d14a065"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-27T11:49:37+00:00`

## Recent changes

- **OPS Knowledge console:** modular UI (overview / source registry / documents / jobs / RAG simulate / media);
- SPEC-010 rewritten; stats API adds `chunks` + `sources_verified`.
- **REQ-008 S2/S3:** Wikipedia + IMSLP + RISM connectors registered; registry revision
- Chunk provenance: `GET /v1/admin/chunks/{id}/provenance` + chunks on document detail/provenance;
- Gates: `tests/test_s2_s3_connectors.py` + registry assertions (23 pytest passed).
- **REQ-008 Authority Source Registry (S1):** versioned `data/registry/sources.yaml` (REG-SRC-001);

## What is working

- **OPS Knowledge console:** modular UI (overview / source registry / documents / jobs / RAG simulate / media);
- SPEC-010 rewritten; stats API adds `chunks` + `sources_verified`.
- **REQ-008 S2/S3:** Wikipedia + IMSLP + RISM connectors registered; registry revision
- Chunk provenance: `GET /v1/admin/chunks/{id}/provenance` + chunks on document detail/provenance;

## What needs attention

- working tree is dirty with 129 tracked or untracked change(s)
- verification gates are not documented yet in EVAL.md
- no explicit next-up slice is recorded

## Durable reminders

- no durable reminders recorded

## Promotion rule

- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset
- do not let retrospective output become the only place where important operating knowledge lives
