---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "checkpoint"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-02T06:53:13+00:00"
effective_status: "active"
effective_since: "2026-08-02T06:53:13+00:00"
content_fingerprint: "sha256:65c2b3ba2bf5997734cb65a5a33b9a7a751e3e19391b4330b518cdbb58859145"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
created_at: "2026-08-02T06:51:16Z"
---
# CKPT — SPEC-034 Slice G multi-work guide sheets

- Status: complete
- Checkpoint time: 2026-08-02T06:51:16Z
- Runtime ids: SPEC-034 Slice G; RCA-2026-08-02-guide-59-multi-work-sheets

## Objective

Support complex multi-work listening guides as one sheet per work plus one
synthesis sheet, with deterministic fan-out/fan-in metadata for future parallel
processing.

## Completed Work

- Extended SPEC-034 with Slice G sheet-mode contract.
- Added RCA report for the guide #59 / release #7083684 failure class.
- Added `guide_sheets[]` and `program_parallel_plan` generation in
  `program_deepen`.
- Preserved sheet fields through `salon_codex` merge and Chinese localization.
- Exposed sheet fields from `listening.synthesize`.
- Rendered sheet tabs inside guide HTML with ARIA roles and keyboard support.
- Bumped `aulos-listening-synthesize` to 0.2.1 and
  `aulos-listening-compose` to 0.3.1.

## In-Progress Work

- None. Local implementation and verification for this slice are complete.

## Next Step

Deploy only after operator approval, then recompose guide #59 and multi-work
Discogs probes to confirm live sheet-mode rendering and persisted
`program_parallel_plan`.

## Blockers/Risks

- No production deploy or live recomposition was requested in this turn.
- Local SQLite does not contain guide id 59; incident evidence is harness/spec
  and release-fixture based.
- Actual parallel execution is not implemented here; this slice only emits the
  worker-safe orchestration plan.

## Verification Performed

- New tests failed before implementation and passed after implementation.
- `cd aulos-skills && .venv/bin/pytest -q tests/test_release_structure.py tests/test_program_deepen.py tests/test_runtime.py tests/test_identity_hygiene.py tests/test_intake_i18n.py tests/test_media_search.py` -> 49 passed.
- `cd aulos-api && PYTHONPATH=. .venv/bin/pytest -q tests/test_discogs.py tests/test_listening_jobs.py tests/test_diary_guides.py` -> 21 passed, 3 warnings.
- `cd aulos-web && npm run build` -> passed.
- Selected `git diff --check` -> passed.

## Verification Still Needed

- Live recomposition of guide #59 after deploy.
- Browser-level visual smoke of a real multi-work guide if the next slice changes
  outer web reader behavior.

## Context State

- Chosen context op: continue. Current slice is complete; future work should
  start from this checkpoint, SPEC-034 §7, and the RCA report.
