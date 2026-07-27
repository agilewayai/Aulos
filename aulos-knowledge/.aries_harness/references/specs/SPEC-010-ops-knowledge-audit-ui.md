---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:33f1edda379e8c6eafeb39088674b173b6e10c08e9199a3213f5435b60796220"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-010 — OPS Knowledge console

## Surface

`aulos-ops` tab **Knowledge** (superadmin) — modular **Knowledge console**.

## Modules

1. **Overview** — plane health, bento metrics (docs/chunks/sources/jobs/artifacts/media), registry gate
   summary, recent jobs, quick navigation.
2. **Source registry** (REQ-008) — table + detail pane; crawl gate visualization (verified + enabled +
   connector); register/verify/reject/suspend/enable; manifest `data/registry/sources.yaml`.
3. **Documents** — query/filter corpus; publish/quarantine proofread; structured provenance cards +
   chunk provenance tabs.
4. **Jobs & crawl** — enqueue catalog + connector crawls; filterable job log table.
5. **RAG simulate** — retrieve lab with presets; work_id/composer_id filters; latency + hit scores.
6. **Media assets** — images/audio/meta table with disk presence observability.

## Transport

Browser → `aulos-api` `/v1/ops/knowledge/*` (JWT) → proxy → `aulos-knowledge`.

## Acceptance

- Operator can observe plane health and corpus metrics without SSH.
- Source registry is a first-class module with visible crawl gates.
- Operator can query documents, verify (publish/quarantine), and audit chunk provenance.
- Operator can simulate RAG retrieve with identity filters.
- Operator can register a source and run catalog_import without SSH.
- Knowledge tab visible only to superadmin (same gate as other ops tabs).
