---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T22:10:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:fd03316d8b89dee69ee8e83ce271aefc9461d90cd7739bc40605423aa9015238"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-034 — Discogs release structure-first pipeline

Implements REQ-024. Upstream covenant: META-001 §4.1. Architecture: ARCH-002, ADR-006.

## 1. Full metadata fetch (unchanged obligation)

`fetch_discogs_entity` / resolve paths must retain the **full** Discogs JSON
(`tracklist`, `extraartists`, `formats`, `labels`, `images`, `genres`, `styles`,
`master_id`, …). Partial “title-only” seeds are insufficient for deepen.

## 2. ReleaseStructure contract

Module: `aulos_skills.release_structure`
Schema: `aulos.release_structure/v1`

| Field | Meaning |
| --- | --- |
| `shape` | `single_work` \| `multi_work_program` \| `shelf` \| `unknown` |
| `program[]` | Clustered works with `title`, `catalog_numbers`, `track_titles`, `instruments_hint` |
| `catalog_numbers_all` | Union of program catalogs |
| `structure_ready` | True only when title + tracklist present and program clustering coherent |
| `gaps` / `ready_reasons` | Explicit diagnostics |
| `expansion_plan` | Layered expand steps (API may attach) |

Clustering rules:

- Tracks with catalog numbers cluster by catalog id (chained BWV/K./Op. via SPEC-033).
- Tracks with no catalogs collapse to one shelf/single program (movements ≠ program works).
- ≥2 distinct catalog works ⇒ `multi_work_program`.

## 3. Emit sites

- `analyze_discogs_release` → `release_structure` + kb_seed provenance summary + RAG program snippets
- `build_diary_snapshot` → `release_structure` on diary posts

## 4. Deepen gate (Slice B)

`assert_structure_ready` / `apply_structure_gate`:

- Multi-work + not ready → `refuse_families=True`, `structure_hard_fails`, critique note
- Intake + IntentLock merge `catalog_numbers_all`
- Process scorecard identity: high finding `release_structure_not_ready` (hard_fail)
- Persist on guide: `release_structure`, `structure_hard_fails`, `program_expand_applied`

## 5. Expansion layers (Slice C → Δ iterative)

| Layer | Name | Goal |
| --- | --- | --- |
| 0 | `release_metadata` | Preserve Discogs credits / formats / URI |
| 1 | `program_map` | Freeze program works + catalogs |
| 2 | `work_deepen` **LOOP** | Gateway `g.program`: for each program work (capped), force web + LLM → `program_iterations[]`; synthesize folds via `fold_program_iterations` → source `release-program-loop` |
| 3 | `pressing_synthesis` | Recording-level interpretations across the shelf |

### 5.1 Why not a single linear pipeline

Album-title web research often `verify_failed` / skips community gather, then album-level
LLM stays on `agent-skills` with a thin family scaffold. That path never visits BWV/K./Op.
landmarks. Multi-work pressings require a **recursive / iterative** deepen:

```text
for work in program[] (max 6):
  run_web_research(work.title, force_action=cold_fill)  # keep rag_hits if verify partial
  optional LLM enrich(work.title)
  append program_iterations
album g.web → skip reason=delegated_to_program_loop
synthesize → fold_program_iterations → finalize_program_dossier (strip generic family map)
```

Rules:

- `force_action` bypasses freshness skip so each work gathers.
- Program titles must be **canonical** (`canonical_discogs_title`) — no Discogs `A = B = C`.
- Search uses `program_search_query` (catalog-first); composer is separate.
- LLM verify/enrich is **optional**: on auth/parse/not-ready → `web_search_raw` floor (persist + fold).
- Album-level `g.web` must not short-circuit the loop when iterations exist.
- Prefer `release-program-loop` over scaffold-only `release-program-expand` when iterations present.
- Fold filters composer-bio / junk hits lacking catalog or work tokens.

## Tests

- Skills: `tests/test_release_structure.py`, `tests/test_program_deepen.py`
- API: `tests/test_discogs.py::test_analyze_emits_release_structure_program`,
  `tests/test_web_research_partial.py`

## 6. Delta 2026-08-02 — fold-back owns final subject

Incident: guide `#59` (`/discogs #7083684`, piano-flute-cello trios) produced a
serious analysis deviation even though `g.program` reported `3/3 works gathered
evidence`. Root mechanism:

- Discogs artist credits named Hummel / Weber / Haydn at release level but program
  works did not retain composer attribution.
- `fold_program_iterations` preserved list chambers, but not final subject
  scalars (`composer`, `listening_thesis`, `work_introduction`, `related_works`,
  pressing synthesis).
- Later album-level LLM and `family:piano-trio` layers could re-generalize the
  dossier.
- API persistence stored `eval_pass=false` as `completed`.

Contract:

1. `ReleaseStructure.program[]` may carry `composers[]`; when Discogs has multiple
   top-level composer-like artists and no explicit per-track composer role, assign
   them positionally only when the counts match the program map. This is an
   inference and must be recorded as such in provenance/ready reasons.
2. `fold_program_iterations` must build final shelf subject text from program
   iterations, preferring per-work titles plus composer names from program entries,
   LLM dossier fields, or release-level composer inference.
3. `finalize_program_dossier` must force program-loop scalar ownership for
   `work_title`, `composer`, `catalog`, `form`, `listening_thesis`,
   `work_introduction`, `related_works`, and `sound_world` when
   `program_loop_applied=true`.
4. Generic family layers remain allowed only as dimensional floors; they may fill
   empty fields but cannot be the final subject of a ready multi-work program.
5. Gateway/API closeout must treat `eval_pass=false`, scorecard hard gates,
   review failure, or required ambient failure as non-completed status while
   preserving guide HTML, steps, research JSON, and trace for revision.

Additional tests:

- Hummel / Weber / Haydn-style release with three program works does not collapse
  to `Unknown composer`, anonymous thesis, or unrelated Mozart related works.
- Persisting a failed-eval report marks the guide failed with actionable
  `error_detail`, not `completed`.

## 7. Delta 2026-08-02 — multi-work sheets + synthesis fan-in

Incident continuation: guide `#59` was not only wrong at final scalar ownership;
it was structurally too thin for a Hummel / Weber / Haydn piano-flute-cello
program. A single essay body cannot carry three independent work identities plus
recording-level comparison without collapsing detail.

Contract:

1. `fold_program_iterations` must emit `guide_sheets[]` when a ready multi-work
   program has two or more program works. The array is ordered:
   one `kind="work"` sheet per program work, followed by one
   `kind="synthesis"` sheet.
2. Each work sheet must preserve identity and listening material:
   `id`, `kind`, `index`, `title`, `composer`, `catalog`, `summary`,
   `listening_map`, `deepdives`, `sound_world`, `source_count`, and
   `llm_source`. A work sheet may degrade to web/craft floor, but it must not
   be empty when the iteration has usable evidence.
3. The synthesis sheet must summarize the complete program, name all work
   identities, and compare the album as a program/pressing rather than replacing
   the works with a generic family essay.
4. The dossier must expose `program_parallel_plan` with deterministic fan-out
   work units and `fan_in="synthesis_sheet"`. This is a planning/observability
   contract in `aulos-skills`; actual worker concurrency belongs to the gateway
   or agent runtime slice and must not share unsafe DB/session objects.
5. `render_bilingual_guide_html` must render `guide_sheets[]` as accessible
   sheet navigation (`role="tablist"`, `role="tab"`, `role="tabpanel"`), with
   stable responsive dimensions and keyboard Arrow/Home/End support inside the
   self-contained guide HTML.
6. The top-level article remains available for legacy readers and SEO-like
   linear reading; the sheet UI is an additional structured reading surface, not
   a replacement for bilingual panes or ambient media.

Additional tests:

- Hummel / Weber / Haydn-style release yields exactly three work sheets plus one
  synthesis sheet; every work sheet names its composer and has map/deepdive cues.
- Rendered guide HTML contains a sheet tablist, selected tab state, all sheet
  panels, and work/synthesis labels.

## 8. Delta 2026-08-02 — budgeted program deepen default

Incident continuation: latest production PostgreSQL guide `#60` for the same
`/discogs #7083684` trio program failed after a long run. The UI appeared to
stall around the third visible step, but PG chain trace showed `g.rag` was
effectively immediate and `g.program` consumed about 711.6 seconds; the
album-level `g.llm` then consumed about 174.6 seconds.

Root mechanisms:

- `g.program` serialized per-work full web gather, optional Agent Reach/Jina,
  web verify LLM, per-work LLM dossier, then an album-level LLM pass.
- `program.deepen_loop` only emitted its milestone at loop completion, making
  the previous visible step look responsible for the delay.
- Rejected/degraded LLM output could leave a JSON string in `llm_note`, which
  `fold_program_iterations` then treated as reader prose.
- `ProductScorecard` did not recognize German instrument tokens in the locked
  title (`Klavier`, `Flöte`, `Violoncello`) and misread historical comparison /
  fortepiano context as solo-instrument substitution.

Contract:

1. Default multi-work program deepen mode is **fast + budgeted**:
   `program_deepen_mode=fast`, `program_deepen_budget_seconds=120`,
   `program_deepen_max_sources=4`, `program_deepen_max_variants=1`,
   `program_deepen_wikipedia_limit=1`, `program_deepen_search_timeout=5`.
2. Fast mode must disable per-work Jina/Agent Reach, web verify LLM, per-work
   LLM dossier, and album-level LLM unless the operator explicitly configures
   full mode or individual overrides.
3. Fast mode still produces a usable work sheet: if web/LLM evidence is weak,
   build an identity floor from program title, composer, catalog, and instrument
   hints; do not emit empty or raw-source caveat prose as the primary subject.
4. `program.deepen_loop` trace facts must record mode, budget, elapsed seconds,
   budget exhaustion, and per-iteration timing so step latency is attributable.
5. `fold_program_iterations` must parse accidental JSON notes before fan-in and
   must never place raw JSON strings into `listening_thesis`, sheet summaries,
   listening maps, or deepdives.
6. Instrument-faithful gates must recognize common Discogs European instrument
   terms for the locked title. Period instrument terms such as `fortepiano` are
   not by themselves evidence of piano-concerto substitution when the title is a
   piano/flute/cello trio.
7. `ambient_ok=false` remains a fail-closed product gate; this delta fixes
   latency, subject thickness, and false instrument drift, not missing media.

Additional tests:

- Default program deepen config is fast/budgeted and disables verify/Jina/LLM.
- Fast web research bypasses LLM verify and Agent Reach while preserving raw
  web evidence.
- German `Klavier / Flöte / Violoncello` title plus `fortepiano` / "replaces
  violin with flute" context does not trigger product solo-instrument drift.
- JSON `llm_note` content is parsed before sheet fan-in.
- Raw-web-only work iterations receive a non-empty identity floor in work
  sheets.
