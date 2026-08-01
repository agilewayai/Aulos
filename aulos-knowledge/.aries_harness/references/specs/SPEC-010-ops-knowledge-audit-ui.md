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
content_fingerprint: "sha256:85ca6f1f83f3c5062fb4a8b381f3f371e4f21327bf5989b8b1229e00dbea99a2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-010 — OPS Knowledge console

## Surface

`aulos-ops` tab **Knowledge** (superadmin) — modular **Knowledge console**.

## Modules

1. **Overview** — plane health, benchmark summary card, bento metrics (docs/chunks/sources/jobs/artifacts/media), registry gate
   summary, recent jobs, quick navigation.
2. **Performance report** — benchmark dashboard: health banner, score trend, dimension breakdown, insights, executive summary.
3. **Source registry** (REQ-008) — table + detail pane; crawl gate visualization (verified + enabled +
   connector); register/verify/reject/suspend/enable; manifest `data/registry/sources.yaml`.
4. **Explore sources** (REQ-009 / META-001 §3.4) — pick a composer from A–Z / Famous strip
   (portraits when crawled); one-click explore; interactive discovery graph; register candidates;
   prepare-seeds for portrait crawl.
5. **Composer dossier** (REQ-010) — life timeline + works tree; build-dossier async crawl;
   browse Bach/Beethoven/Mozart-class dossiers without QIDs in the primary path.
6. **Documents** — query/filter corpus; publish/quarantine proofread; structured provenance cards +
   chunk provenance tabs.
7. **Jobs & crawl** — enqueue catalog + connector crawls; filterable job log table.
8. **RAG simulate** — retrieve lab with presets; work_id/composer_id filters; latency + hit scores.
9. **Benchmark** — KB-BENCH-001: run evaluation, dimension scores, run history, markdown report.
10. **Diagnose & improve** — KB-DIAG/KB-IMPROVE: findings, L1 auto crawl, L3 engineering tasks, improve cycle.
11. **Media assets** — images/audio/meta table with disk presence observability.

## Transport

Browser → `aulos-api` `/v1/ops/knowledge/*` (JWT) → proxy → `aulos-knowledge`.

## Acceptance

- Operator can observe plane health and corpus metrics without SSH.
- Source registry is a first-class module with visible crawl gates.
- Operator can query documents, verify (publish/quarantine), and audit chunk provenance.
- Operator can simulate RAG retrieve with identity filters.
- Operator can run knowledge benchmark and view score history + markdown report.
- Operator can open performance dashboard report with trend and actionable insights.
- Operator can run diagnose → safe crawl actions → full improve cycle with score delta.
- Operator can register a source and run catalog_import without SSH.
- Operator can explore authority sources via graph search and register candidates.
- Operator can build and browse a composer life timeline and works tree (REQ-010).
- Knowledge tab visible only to superadmin (same gate as other ops tabs).
