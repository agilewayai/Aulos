---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "run-report"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-02T09:44:23Z"
effective_status: "active"
effective_since: "2026-08-02T09:44:23Z"
content_fingerprint: "sha256:17d91c0484e37bc5ab83147e4f782dc3547066ba1fd5acd4ed22c090e81ce00d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
created_at: "2026-08-02T09:44:23Z"
---
# RCA — guide #60 piano / flute / cello trio failure and program deepen budget

## Scope

This report covers the latest production PostgreSQL listening-guide row for the
Hummel / Weber / Haydn piano-flute-cello trio Discogs pressing:

- guide id: `60`
- Discogs release: `7083684`
- title: `Trios Für Klavier, Flöte Und Violoncello`
- status: `failed`
- source: `agent-skills+deepseek`
- error: `eval_pass=false; ambient_ok=false`
- created: `2026-08-02T07:33:18Z`
- updated: `2026-08-02T07:48:26Z`
- `guide_html` length: `113101`

Evidence source is the production PostgreSQL primary on
`127.0.0.1:5433/aulos` via the host `AULOS_DB_URL` setting. The credentialed
connection string is intentionally not recorded in this report.
SQLite was not inspected or used for this incident.

## What Failed

The guide failed for two visible product reasons:

1. Product eval did not pass.
2. Ambient media was absent (`ambient_ok=false`).

The failure was amplified by three root mechanisms:

1. The visible "step 3" looked slow, but the actual slow stage was not RAG.
2. Multi-work program deepen used an over-heavy default path for a synchronous
   guide job.
3. The product scorecard treated historically correct instrument comparison as
   a title-instrument betrayal.

## PostgreSQL Chain Evidence

`research_json.chain_trace.milestones` shows the real timing:

| Stage | UTC | Delta |
| --- | --- | --- |
| `discogs.resolve` | `2026-08-02T07:33:19Z` | - |
| `discogs.structure` | `2026-08-02T07:33:20Z` | about 1.5s |
| `rag` | `2026-08-02T07:33:20Z` | about 0.004s |
| `program.deepen_loop` | `2026-08-02T07:45:12Z` | about 711.6s |
| `web_research` | `2026-08-02T07:45:12Z` | skipped, delegated |
| `llm_enrich` | `2026-08-02T07:48:06Z` | about 174.6s |
| `persist` | `2026-08-02T07:48:26Z` | final failed row |

Conclusion: the user's "third step feels slow" observation is real from the UI
perspective, but the backend slow segment is `g.program` after `g.rag`, not the
RAG/Knowledge stage itself. Because `g.program` only produced its completion
milestone after the loop, the UI could continue to look like it was still on the
previous visible step.

## Root Cause 1 — Over-heavy Program Deepen Default

Before this slice, `g.program` iterated works serially. For each program work it:

- forced `run_web_research(..., force_action="cold_fill")`;
- allowed the normal web gather path to use multiple Wikipedia variants,
  DuckDuckGo, optional Brave, and Agent Reach / Jina page deepen;
- ran LLM verification for web dossier extraction;
- then ran per-work `_optional_llm_dossier` with a 90s timeout;
- then the album-level `g.llm` could run another 90s LLM enrichment.

For a 3-work pressing, the default path could therefore compound network search,
Jina, web-verify LLM, per-work LLM, and album LLM serially. That is over-designed
for the default production guide path.

The architectural principle remains correct: release structure before deepen,
work-local fan-out, then synthesis fan-in. The implementation default was wrong:
it used "full research mode" where the product needed a bounded fast evidence
floor.

## Root Cause 2 — JSON / Weak Text Entered Product Sheets

PG `guide_sheets[]` showed that the Hummel sheet summary and top-level thesis
contained a raw JSON string from an LLM note / rejected dossier path, for example
`{"work_title": ... "listening_thesis": ...}` fragments.

This happened because a rejected or degraded LLM path could leave useful JSON in
`llm_note`, but `fold_program_iterations` treated that note as prose. The
fan-in layer then copied JSON text into the sheet summary, listening map, and
top-level thesis. When web evidence was only composer biography, the subject also
became thin.

## Root Cause 3 — Instrument Drift Gate Was Too Narrow

The locked Discogs title uses German instrument terms:

- `Klavier` = piano
- `Flöte` = flute
- `Violoncello` = cello

The prior instrument gate did not recognize these title tokens. It then saw
`fortepiano` and historical comparison phrases such as "Haydn replaces the
violin with a flute" and flagged:

`product_solo_instrument_drift: Product prose substitutes a different solo instrument than the locked title`

That was a false positive for this title. The prose was explaining period
instrument culture and an alternate flute-trio scoring, not substituting the
guide's locked title with another solo instrument.

## Ambient Gate

`ambient_ok=false` remains a real product gate. This slice does not loosen it.
If no work-matched audio/video is available, the guide should continue to fail
closed or stay unpublished until a media candidate is supplied or found by a
separate media pipeline.

## Implemented System Fix

### API / Gateway

- Added `web.research` program-deepen controls:
  - `program_deepen_mode`: default `fast`, optional `full`;
  - `program_deepen_budget_seconds`: default `120`;
  - `program_deepen_max_sources`: default `4`;
  - `program_deepen_verify_sources`: default `false`;
  - `program_deepen_per_work_llm`: default `false`;
  - `program_deepen_album_llm`: default `false`;
  - `program_deepen_agent_reach_enabled`: default `false`;
  - `program_deepen_max_variants`: default `1`;
  - `program_deepen_wikipedia_limit`: default `1`;
  - `program_deepen_search_timeout`: default `5.0`.
- `run_web_research` now supports fast raw-web mode:
  - bypass LLM verify when requested;
  - disable Agent Reach / Jina per call;
  - cap source count, query variants, and search timeout per call.
- `g.program` now records mode, budget, elapsed seconds, per-iteration timings,
  and whether the budget was exhausted.
- Ready multi-work programs skip album-level `g.llm` in fast mode because the
  program fan-in owns the final subject.

### Skills / Product

- `program_deepen` parses accidental JSON notes before fan-in.
- It suppresses raw JSON / web-caveat prose from sheet summaries.
- It adds a deterministic identity floor from composer, title, catalog, and
  instrument hints when web/LLM evidence is weak.
- It recognizes German / common European instrument tokens such as `Klavier`,
  `Flöte`, `Violoncello`, `clavier`, `flauto`, and `violoncelle`.
- The solo-instrument drift gate no longer treats bare `fortepiano` period
  instrument prose as a piano-concerto substitution.

## Verification

Red tests added before implementation:

- `aulos-api/tests/test_web_research_partial.py`
  - `test_program_deepen_config_defaults_to_fast_budget`
  - `test_fast_program_research_bypasses_verify_and_agent_reach`
- `aulos-skills/tests/test_instrument_faithful_thicken.py`
  - `test_product_scorecard_allows_german_flute_cello_piano_trio_context`
- `aulos-skills/tests/test_program_deepen.py`
  - `test_fold_iterations_parses_json_note_before_sheet_fanin`
  - `test_fold_iterations_uses_identity_floor_for_raw_web_only_sheet`

Focused results:

```bash
cd aulos-api && .venv/bin/pytest -q tests/test_web_research_partial.py
# 4 passed

cd aulos-skills && .venv/bin/pytest -q tests/test_program_deepen.py tests/test_instrument_faithful_thicken.py
# 20 passed
```

## Remaining Risk

- This slice makes the default production path bounded and cleaner; it does not
  implement true parallel worker execution. `program_parallel_plan` remains the
  deterministic plan contract for a later worker-safe fan-out/fan-in slice.
- A future media slice should add better work-matched video/audio discovery or
  operator curation so `ambient_ok=false` is less common without weakening the
  product gate.
