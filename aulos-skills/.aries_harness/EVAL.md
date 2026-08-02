---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "evaluation"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "CKPT-005"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T16:10:00Z"
content_fingerprint: "sha256:66b2dd2f815d28bd10237d9afb2596bdca8327c23e0b56eeba2d62b71ee6550a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- unit (skills): `cd aulos-api && .venv/bin/python -m pytest ../aulos-skills/tests/test_runtime.py ../aulos-skills/tests/test_ambient_agent.py ../aulos-skills/tests/test_ambient_playlist.py -q`
- unit (process scorecard): `cd aulos-skills && python -m pytest tests/test_process_scorecard.py -q`
- unit (identity hygiene / guide #48): `cd aulos-skills && python -m pytest tests/test_identity_hygiene.py -q`
- unit (external review round / SPEC-022): `cd aulos-skills && python -m pytest tests/test_external_review_round.py tests/test_review_targets.py tests/test_targeted_revise.py -q`
- unit (product-prose hygiene / SPEC-023): `cd aulos-skills && python -m pytest tests/test_prose_hygiene.py tests/test_external_review_hygiene.py -q`
- unit (craft raise / SPEC-024): `cd aulos-skills && python -m pytest tests/test_craft_raise.py -q`
- unit (knowledge thicken + ProductScorecard / SPEC-025): `cd aulos-skills && python -m pytest tests/test_knowledge_product_score.py tests/test_marker_boundaries.py -q`
- unit (systemic cold thicken / SPEC-026): `cd aulos-skills && .venv/bin/python -m pytest tests/test_systemic_cold_thicken.py -q`
- unit (family coverage / SPEC-027): `cd aulos-skills && .venv/bin/python -m pytest tests/test_family_coverage.py -q`
- unit (catalog craft + fleet dossier / SPEC-028): `cd aulos-skills && .venv/bin/python -m pytest tests/test_catalog_craft_coverage.py -q` ；`cd aulos-api && .venv/bin/python -m pytest tests/test_ensure_composer_dossiers.py -q`
- unit (unknown-case thicken / SPEC-029): `cd aulos-skills && .venv/bin/python -m pytest tests/test_unknown_case_thicken.py -q`
- unit (promote staging / SPEC-030): `cd aulos-skills && .venv/bin/python -m pytest tests/test_promote_staging.py -q` ；`cd aulos-api && .venv/bin/python -m pytest tests/test_promote_stage_api.py -q`
- unit (dimensional promote / SPEC-031): `cd aulos-skills && .venv/bin/python -m pytest tests/test_dimensional_promote.py -q` ；`cd aulos-api && .venv/bin/python -m pytest tests/test_promote_production_api.py -q`
- unit (Discogs release-structure-first / SPEC-034): `cd aulos-skills && .venv/bin/pytest -q tests/test_release_structure.py tests/test_program_deepen.py tests/test_runtime.py`; render/identity adjunct: `cd aulos-skills && .venv/bin/pytest -q tests/test_identity_hygiene.py tests/test_intake_i18n.py tests/test_media_search.py`; consumer gate: `cd aulos-api && PYTHONPATH=. .venv/bin/pytest -q tests/test_discogs.py tests/test_listening_jobs.py tests/test_diary_guides.py`
- unit (SPEC-034 Slice H latency / instrument drift): `cd aulos-skills && .venv/bin/pytest -q tests/test_program_deepen.py tests/test_instrument_faithful_thicken.py`; API budget gate: `cd aulos-api && .venv/bin/pytest -q tests/test_web_research_partial.py`
- unit (media API): `cd aulos-api && .venv/bin/python -m pytest tests/test_media.py -q`
- media smoke: `curl -sI 'http://127.0.0.1:5090/v1/media/audio?src=<urlencoded-commons-url>&mode=cache' | grep -i content-disposition` → must contain `inline`
- live parity: recompose Goldberg + one cold-path Chinese work; assert bilingual + ambient in `guide_html`

## Acceptance notes

Minimum gate for listening compose/eval:

1. Salon Codex chambers present (composer / anatomy / practice / map).
2. Bilingual panes when `zh` pack exists (`data-lang="zh"` + `data-lang="en"`).
3. Ambient player present when resolved (`id="aulos-ambient"` / `data-ambient-player`);
   missing ambient is a **soft** score note (not hard-fail alone). Embed mode uses
   `data-ambient-player="v2-embed"`.
4. No foreign flagship leak (Goldberg markers absent from non-Goldberg works).
5. Media served `inline` via `/v1/media/audio` (cache preferred).

### Process scorecard (SPEC-019)

6. Each scored skill node appends a `NodeScorecard` to `node_scorecards`.
7. Eval writes `process_scorecard` (`aulos.process_scorecard/v1`) with rollup.
8. Clean Catalog path: `rollup.pct >= 70` and `rollup.band` ∈ {solid, strong} when ambient+bilingual present.
9. `review_failed` ⇒ fidelity hard_fail and `gates.review_failed=true`.
10. N/A dimensions must not reduce earned/max (excluded from pct).
11. Portrait / foreign-family dossier_id / H1 title drift ⇒ identity hard_fail; high findings
    append into `critique_corrections` for multi-agent rework (`tests/test_identity_hygiene.py`).
12. SPEC-022Δ: targeted revise + `revision_history`; dual draft scorecards
    (`tests/test_external_review_round.py`, `test_review_targets.py`, `test_targeted_revise.py`).
13. SPEC-023: no `CRITIQUE LOCK` / `REVIEW REPAIR` in product HTML; packaging titles cleaned;
    EN layer not mostly-CJK; review drops empty-body hallucinations when dossier is rich
    (`tests/test_prose_hygiene.py`, `tests/test_external_review_hygiene.py`).
14. SPEC-024: Work Resolver locks Catalog `work_id` on cleaned Discogs titles; chamber
    contracts enforce craft floors + ZH parity; cold family thicken registered
    (`tests/test_craft_raise.py`).
15. SPEC-025: ProductScorecard in `research_json`; `eval_pass` follows product band;
    knowledge-plane thicken and/or craft pack visible in `synthesize_source`; digit
    alien markers use word boundaries (`tests/test_knowledge_product_score.py`,
    `tests/test_marker_boundaries.py`).
16. SPEC-026: Catalog craft floor for any `work_id`; thin knowledge dossier auto-enqueues
    build; ProductScorecard `asset_depth` — family-only cannot be `strong`
    (`tests/test_systemic_cold_thicken.py`).
17. SPEC-027: every Catalog work has registered `family_id`; genre packs for concerto /
    requiem / symphony / trio; synthesize prefers Catalog family lock
    (`tests/test_family_coverage.py`).
18. SPEC-028 (superseded thicken path): craft packs are **optional** promote-pipeline
    outputs, not required Catalog coverage. Synthesize uses `catalog-floor:` without
    hand craft YAML (`tests/test_catalog_craft_coverage.py`).
19. SPEC-029: unknown (non-Catalog) titles thicken via FacetClassifier → `archetype:{id}`
    (not bare `generic-scaffold`); `promote_candidate` dry-run schema when chamber floors
    pass (`tests/test_unknown_case_thicken.py`).
20. SPEC-030: operator stages promote_candidate into `craft/staging/` (not production);
    ops list/stage + Guide quality Stage; classifier covers prelude/etude/ballade/quartet
    (`tests/test_promote_staging.py`, `aulos-api/tests/test_promote_stage_api.py`).
21. SPEC-031: dimensional templates `(instruments × forms × era)` + generic
    promote-to-production; **anti-case** — ≥2 unrelated identities on same path; META-001 v6
    (`tests/test_dimensional_promote.py`, `aulos-api/tests/test_promote_production_api.py`).
22. Compression (2026-08-01): deleted pre-authored per-work craft YAML and case-hardcoded
    review marker lists (Bernstein / K.488 / Op.69 / rival composers / beethoven.jpg);
    foreign-chamber detection uses form_lock policy only.
23. SPEC-034 Slice F: structure-ready multi-work programs must carry per-work composer
    into `g.program`; `release-program-loop` owns final subject scalars
    (`composer`, thesis, introduction, related works, sound world); failed eval/process
    gates must not persist or publish as completed guides.
24. SPEC-034 Slice G: structure-ready multi-work programs with iterations expose
    `guide_sheets[]` (work sheets + synthesis sheet), `program_parallel_plan`
    (`fan_out` + `fan_in=synthesis_sheet`), and rendered HTML sheet tabs with
    `role="tablist"` / `role="tab"` / `role="tabpanel"` plus keyboard support.
25. SPEC-034 Slice H: default `g.program` is fast/budgeted for production:
    no per-work Jina, web verify LLM, per-work LLM, or album LLM unless full
    mode is explicitly enabled; trace records mode/budget/elapsed/timings.
    Fan-in must parse JSON notes before product prose, build identity floors
    for raw-web-only work sheets, and must not flag German piano/flute/cello
    trio titles as solo-instrument drift because of fortepiano or historical
    violin-comparison prose.

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
- production deploy evidence:
  `runs/deployments/DEPLOY-2026-08-02-spec-034-slice-g-production.md`
- RCA:
  `runs/reports/RCA-2026-08-02-guide-60-program-deepen-budget.md`
- checkpoint: `checkpoints/CKPT-005-ambient-identity-gates.md`
- insights: `docs/insights.md`
