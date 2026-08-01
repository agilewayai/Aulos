---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:30:00Z"
content_fingerprint: "sha256:1364fc04c0e98b761b7d22c2dfc1935900adc6f11ea0133c053e55fea1917022"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-020 — Promote staging + operator surface (Unknown-Case v2)

## Problem

SPEC-029 emits `promote_candidate` dry-run only. Operators cannot see or stage
survivors into craft caches. FacetClassifier token coverage is thin for common
Discogs form labels.

## Outcomes

1. **Staging craft write** — operator-approved write of craft YAML under
   `craft/staging/{suggested_work_id}.yaml` (never auto-write production
   `craft/` in this REQ).
2. **Ops list + apply** — list guides with promote candidates; apply stages
   craft and marks `promote_candidate.status=staged`.
3. **Trace/UI surface** — guide trace carries promote + product asset signals;
   Guide quality panel can stage.
4. **Classifier thicken** — expand form/instrument tokens for common Discogs
   unknown titles (prelude, etude, ballade, quartet, …).

## Non-goals

- Auto Catalog work registration.
- Auto production craft overwrite without explicit future REQ.
- Blocking compose on staging presence.

## Acceptance

- Unit: `tests/test_promote_staging.py` (+ classifier expansion cases).
- API: list/apply promote endpoints; staging file exists after apply.
- Ops: Guide quality shows promote draft + Stage action.
