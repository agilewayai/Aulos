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
generated_at: "2026-07-27T09:44:33+00:00"
effective_status: "generated"
effective_since: "2026-07-27T09:44:33+00:00"
content_fingerprint: "sha256:d730fb1602a2f43fdc00e5e06725b634ba49101d536b82f2cd8fa24bae0f0365"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-27T09:44:33+00:00`

## Journal milestones

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

### 2026-07-26T17:00:00Z

- SPEC-008 delta: `suggest_discogs_releases` + authenticated `GET /v1/discogs/search` AJAX autocomplete
- Classical-first hit ranking; catno + free-text search; no full release fetch until compose
- Verify: `.venv/bin/pytest tests/test_discogs.py` 8 passed

### 2026-07-26T17:05:00Z

- SPEC-011: Redis mail queue `aulos:mail:queue` + background worker; live verify/reset async
- Fake mail stays sync; Mailgun probe stays sync; Redis fail → daemon thread fallback
- Ops `GET /v1/ops/mail/queue`; verify: `pytest tests/test_mail_queue.py` (+ auth/mailgun) 18 passed

## Recent git commits

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
- `M` `README.md`
- `M` `aulos-api/.aries_harness/ARIES_HARNESS_FINGERPRINT.json`
- `M` `aulos-api/.aries_harness/EVAL.md`
- `M` `aulos-api/.aries_harness/INDEX.md`
- `M` `aulos-api/.aries_harness/JOURNAL.md`
- `M` `aulos-api/.aries_harness/STATE.md`
- `M` `aulos-api/.aries_harness/TASK_STACK.md`
- `M` `aulos-api/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- `M` `aulos-api/.aries_harness/history/DOC_TRACE.md`
- `M` `aulos-api/.aries_harness/history/README.md`
