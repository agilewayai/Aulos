---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "run-report"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-02T06:53:13+00:00"
effective_status: "active"
effective_since: "2026-08-02T06:53:13+00:00"
content_fingerprint: "sha256:aeaf0696770a4c8102ebe2f052996eb88b046d7f50cb345eecbb49559dff6e23"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
created_at: "2026-08-02T06:50:14Z"
---
# RCA — guide #59 multi-work trio deviation and sheet-mode upgrade

## Scope

This report covers the listening-guide failure class behind the recent
piano / flute / cello trio Discogs guide (`/discogs #7083684`, guide #59 in the
active harness record): Hummel / Weber / Haydn program works were structurally
present in the middle of the pipeline, but the final guide body still drifted
into a thin, generic subject.

Local SQLite in this checkout does not contain guide id 59; the local
`aulos-api/data/aulos.db` latest row is id 46. Evidence here therefore uses the
current SPEC-034 incident record, the release #7083684 fixtures, and executable
regression tests.

## Failure Mode

The user-visible symptom was not just a bad paragraph. It was a whole-chain
contract failure:

1. Discogs identified a classical pressing containing multiple works for the
   same ensemble forces: piano, flute, and cello.
2. Mid-pipeline program deepen gathered evidence for the individual works.
3. The final product had a single dominant essay body and scalar identity fields.
4. Later album / family / LLM layers could still re-own final subject fields.
5. The rendered guide did not give each work its own structural reading surface.
6. API persistence previously allowed failed quality/eval states to appear
   completed, making operator diagnosis harder.

## Chain Analysis

### Intake / Identity

The release title is album-level packaging, not a work title. For this class of
Discogs pressing, identity must be resolved as a program map before any thicken
or family scaffold. SPEC-034 already moved the system toward
`ReleaseStructure.program[]`, but guide #59 exposed that the program entries
also needed composer ownership.

Root cause: release-level composer-like artists were not guaranteed to become
per-work composers. Without per-work composer identity, the final guide could
fall back to `Unknown composer` or anonymous shelf language.

### Structure / Deeper Research

The correct model is fan-out by work:

```text
program_map -> work_deepen(Hummel Op. 78)
            -> work_deepen(Weber Op. 63)
            -> work_deepen(Haydn Hob. XV:16)
            -> synthesis fan-in
```

The old product shape still looked like a linear single-work pipeline:

```text
release -> corpus -> synthesize -> compose -> one article body
```

Root cause: the system had `program_iterations[]`, but not a product-grade
`guide_sheets[]` contract. Correct mid-chain data therefore had no guaranteed
place in the final user-facing surface.

### Synthesize / Merge

The program loop produced useful list chambers, but final scalar fields
(`composer`, `listening_thesis`, `work_introduction`, `related_works`,
`sound_world`) remained vulnerable to later generic layers.

Root cause: a correct middle stage was treated as another merge input rather
than as final subject owner for ready multi-work programs.

### Compose / Frontend Surface

The guide renderer could only express multi-work material as ordinary lists
inside the same article. That makes three independent works compete for one
lede, one map, and one deep-dive section.

Root cause: the product did not have a navigation shape for complex programs.
The frontend iframe is a suitable secure container, but the guide HTML itself
needed accessible sheet navigation.

### Evaluation / Persistence

If a guide fails final eval or process gates, storing it as completed hides the
run state from operators and makes bad output look publishable.

Root cause: gate status and product persistence were not fail-closed enough for
multi-stage listening jobs. Slice F already addressed this in the API path; this
Slice G makes the product structure less likely to fail the same way.

## Meta Root Cause

The systemic problem was a mismatch between data shape and product shape.

The program was inherently plural, but the final guide contract was singular.
When plural evidence was forced through singular fields, the system had to
choose a single dominant subject. That choice was unstable: it could become the
album title, a generic family, an anonymous composer, or an unrelated carryover.

The durable fix is not more prompt wording. The durable fix is a higher-order
contract:

- structure first: identify the program before thicken;
- work-local fan-out: deepen each work under its own identity;
- synthesis fan-in: compare only after identities are locked;
- render plural structure: expose one sheet per work plus synthesis;
- fail closed: do not publish bad gate outcomes as completed.

## Implemented Upgrade

### Data Contract

`fold_program_iterations` now emits:

- `guide_sheets[]`
  - `kind="work"` for each program work
  - `kind="synthesis"` for the final overview
- `program_parallel_plan`
  - schema: `aulos.program_parallel_plan/v1`
  - mode: `fan_out_fan_in`
  - fan-out units: work index, title, composer, catalog numbers, search query,
    and target sheet id
  - fan-in: `synthesis_sheet`

### Merge / Runtime

`salon_codex.merge_dossiers` now preserves `guide_sheets` and
`program_parallel_plan`. `finalize_program_dossier` forces these fields from the
program loop when `program_loop_applied=true`. `listening.synthesize` exposes
them both inside `corpus_dossier` and as top-level outputs for observers and
future gateway orchestration.

### Render / UI

`render_bilingual_guide_html` renders `guide_sheets[]` as tabs inside each
language pane:

- `role="tablist"`, `role="tab"`, `role="tabpanel"`;
- selected state via `aria-selected` and `tabindex`;
- ArrowLeft / ArrowRight / ArrowUp / ArrowDown / Home / End keyboard support;
- stable horizontal tab row, no outer React duplication;
- existing iframe sandbox remains the security boundary.

### Skill Surface

- `aulos-listening-synthesize` bumped to `0.2.1`.
- `aulos-listening-compose` bumped to `0.3.1`.
- Both skill docs now state the multi-work sheet contract.

## Verification

Red tests added before implementation:

- `test_fold_iterations_builds_work_sheets_and_synthesis`
- `test_render_multi_work_sheets_as_accessible_tabs`

Commands run:

```bash
cd aulos-skills && .venv/bin/pytest -q tests/test_program_deepen.py -k 'work_sheets or accessible_tabs'
cd aulos-skills && .venv/bin/pytest -q tests/test_release_structure.py tests/test_program_deepen.py
cd aulos-skills && .venv/bin/pytest -q tests/test_runtime.py
cd aulos-skills && .venv/bin/python -m py_compile src/aulos_skills/program_deepen.py src/aulos_skills/guide_render.py src/aulos_skills/salon_codex.py src/aulos_skills/i18n.py src/aulos_skills/runtime.py
cd aulos-skills && .venv/bin/pytest -q tests/test_release_structure.py tests/test_program_deepen.py tests/test_runtime.py tests/test_identity_hygiene.py tests/test_intake_i18n.py tests/test_media_search.py
cd aulos-api && PYTHONPATH=. .venv/bin/pytest -q tests/test_discogs.py tests/test_listening_jobs.py tests/test_diary_guides.py
cd aulos-web && npm run build
```

Observed results:

- New red tests failed before implementation, then passed.
- `aulos-skills` targeted / adjacent tests: 49 passed.
- API consumer gates: 21 passed, 3 warnings.
- Web build: passed.

## Remaining Work

- At original local slice close, no production deploy had been performed.
- Live guide #59 was not recomposed in this slice because guide regeneration /
  live content mutation was not requested.
- Actual concurrent execution should be implemented later in the gateway or
  agent runtime with worker-safe state isolation. This slice emits the safe
  deterministic plan and product contract; it does not run DB-backed per-work
  jobs in parallel inside one HTTP/session context.

## Deployment Follow-up

2026-08-02T07:24:00Z: operator requested production deployment. The current
dirty tree was deployed and production status/smoke passed. Evidence:
`../deployments/DEPLOY-2026-08-02-spec-034-slice-g-production.md`. Live guide
#59 recomposition and browser-level visual smoke remain pending.
