---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:43Z"
generated_at: "2026-07-27T10:25:06+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:06+00:00"
content_fingerprint: "sha256:12ceba28b3e908d2c819ff6fe64d91a5f461b11ef67578109e688d65beeac2ad"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-27T10:25:06+00:00`

## Journal milestones

### 2026-07-27T10:30:00Z

- SPEC-018: Ops background task queue — `ops_tasks` table, Redis `aulos:ops:tasks:queue`, worker in lifespan.
- Dev blog generate/regenerate → **202** enqueue `dev_blog.generate`; sync mode for tests (`AULOS_TASK_QUEUE_SYNC`).
- API: `GET /v1/ops/tasks/dashboard`, `/tasks`, `/tasks/{id}`; dashboard aggregates mail + listening + ops.
- Ops UI: **Tasks** tab (`TaskQueuePanel`), Dev Blog panel polls task completion.
- Gates: `tests/test_task_queue.py`, `tests/test_dev_blog.py` (8 passed).

### 2026-07-27T10:15:00Z

- SPEC-017: Dev Blog **internal writing contract** — evidence-only, factual dev trace; no hype/emotion/external marketing.
- `dev_blog_contract.py`: SYSTEM_PROMPT rewrite + `validate_dev_blog_body()` soft lint; fake draft aligned.
- Promoted into SPEC-009, ops SPEC-002, REQ-002, `aulos-operating-defaults`, Ops UI lead copy.

### 2026-07-26T19:20:00Z

- Root cause: `merge_dossiers` called bare `dict(zh_hans)` when LLM/web returned prose/list →
- Fix: `coerce_dict()` + harden merge/parse/runtime/KB; gate `tests/test_salon_codex_merge.py`.

### 2026-07-26T19:10:00Z

- SPEC-013 delta: countable listening-chain plan (15 stages) seeded in `steps_json`; gateway emits live stage updates; SSE `progress` snapshots for reconnect.
- Robust recovery: client SSE reconnect + hydrate; `POST /{id}/retry` for failed/stale jobs; Atelier progress bar + Retry chain.
- Gates: `tests/test_listening_plan.py`, `tests/test_listening_jobs.py`; web `npm run build`.

### 2026-07-26T18:20:00Z

- Operating rule: every model-shape slice must close with dual-dialect `schema_patches` + PG verify (SQLite pilot ≠ production).
- Added `aulos_api.db.schema_patches`; HA/init apply on Postgres+SQLite. Migrated live PG SPEC-013 columns (`message`, `tags_json`, `favorited_at`, …).
- Gate: `tests/test_schema_patches.py`; promoted insight + `aulos-operating-defaults` section.

### 2026-07-26T18:15:00Z

- SPEC-013: durable listening-guide jobs (`queued`→`running`→`completed|failed`), Redis/`thread` worker (`listening_queue.py`), reconnect-safe `GET …/events`.
- Library: DELETE, list `q`/`status`/`published`/`favorited`/`tag`, favorite + tags.
- Legacy `/stream` and recompose/stream enqueue then attach to job events (no long-held DB session).
- Verify: `pytest tests/test_listening_jobs.py` + stream/recompose SSE green.

### 2026-07-26T17:20:00Z

- SPEC-012: per-run `chain_trace` (aulos.chain_trace/v1) in research_json for 复盘
- Milestones: discogs → identity → lock → rag → web → llm → skill.intake/synthesize → persist
- Auto deviations: composer/title drift, family_without_work_id
- Routes: owner `GET /v1/listening-guides/{id}/trace`, ops `GET /v1/ops/listening-guides/{id}/trace`
- Verify: `pytest tests/test_chain_trace.py` 4 passed

### 2026-07-26T17:10:00Z

- Discogs intent rewrite avoids `I'm listening to…` intake trap; Discogs title/composer always win over weak Catalog
- Companion fix in aulos-skills family composer gate (Mozart K.488 no longer inherits Beethoven cello pack)
- Verify: `pytest tests/test_discogs.py` 8 passed; live `/discogs #6280908` synthesize=`kb-rag` only

## Recent git commits

- `c3009d2` 2026-07-27 Harden platform security, ship fleet DevOps control, and refresh harness honeycomb.
- `0c8a847` 2026-07-27 Ship Ops daily Dev Blog and web forgot-password reset.
- `6ab1ea3` 2026-07-26 Ship /discogs release and catalog-number listening guides with OPS token UI.
- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `AGENTS.md`
- `M` `CLAUDE.md`
- `M` `aulos-api/.aries_harness/ARIES_HARNESS_FINGERPRINT.json`
- `M` `aulos-api/.aries_harness/INDEX.md`
- `M` `aulos-api/.aries_harness/JOURNAL.md`
- `M` `aulos-api/.aries_harness/STATE.md`
- `M` `aulos-api/.aries_harness/references/REG-001-artifact-register.md`
- `M` `aulos-api/.aries_harness/references/specs/SPEC-008-discog-release-guide.md`
- `M` `aulos-api/.aries_harness/references/specs/SPEC-009-ops-dev-blog.md`
- `M` `aulos-api/src/aulos_api/app.py`
- `M` `aulos-api/src/aulos_api/config/settings.py`
- `M` `aulos-api/src/aulos_api/db/models.py`
