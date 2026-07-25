---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "story-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:25:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:22:35+00:00"
content_fingerprint: "sha256:0770308f0d05789da8cf479af8db2d3e7fe7d4ce1de494226fd3c43a1179405a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# STORY-PACK-007 — Music knowledge plane (longrun)

Upstream: REQ-007, SPEC-009, SPEC-010, ARCH-005, ADR-005/006  
Checkpoint: CKPT-007  
Mode: longrun + coding-loop (Inspect → Plan → Edit → Verify → Summarize)

## Slices

| ID | Intent | Verify first | Status |
| --- | --- | --- | --- |
| S0 | Harness longrun surface (STATE, TASK_STACK, CKPT, REG) | Checkpoint contract sections present | **done** |
| S1 | Postgres/pgvector path docs + compose; SQLite tests green | `pytest tests/` green; PG smoke when compose up | **done** (PG smoke SKIP recorded) |
| S2 | RAG passes Catalog `work_id` into knowledge retrieve | Cello work_id hits ≠ Goldberg-only docs | **done** |
| S3 | Worker/retry notes; disabled source → 400; failed job status | Existing + job failure test | **done** |
| S4 | OPS empty-state when knowledge plane down | SPEC-010 checklist | **done** |
| S5 | Closeout VR + insights + history-refresh | JOURNAL + history/daily | **done** |

## Cadence

- Progress every 30 minutes while coding
- Update CKPT-007 at each slice boundary
- Context op: continue | compact | new-thread

## Non-goals

- Discogs/IMSLP full connectors
- Replacing Catalog identity with KB
- Migrating business `aulos.db` to Postgres
