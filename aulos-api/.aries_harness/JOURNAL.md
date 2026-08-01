---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "journal"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:43Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:43Z"
content_fingerprint: "sha256:e36ea709441bec34661289b00cae339a08ff3439d700ddd0b89948ac94481768"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-08-01T06:35:00Z

- **SPEC-018 delta:** ops task type `knowledge.benchmark` (+ improve path) via knowledge plane proxy;
  `POST /v1/ops/knowledge/benchmark/run` enqueues durable ops task; gate
  `tests/test_knowledge_benchmark_task.py`.
- Honeycomb closeout with knowledge/ops knowledge-console ship.

## 2026-07-27T10:45:00Z

- Cross-ref **AUDIT-009** remediation (primary journal: `aulos-skills/.aries_harness/JOURNAL.md`, review `runs/reviews/AUDIT-009-…`):
  - F3 SPEC-014 HttpOnly session cookie; F2 SPEC-015 guide HTML security + sanitizer; F10 SPEC-016 module splits; F11 ADR-008 plaintext secrets accepted for Sprint-1.
  - Fleet DevOps: `deploy/aulos-ctl.sh`, `deploy/OPS.md`, `deploy/honeycomb.sh` (commit `c3009d2`).
- Dev-blog evidence fix: `_journal_slice_for_day` now keeps **newest** day entries (was truncating tail → dropped AUDIT slices).

## 2026-07-27T10:30:00Z

- SPEC-018: Ops background task queue — `ops_tasks` table, Redis `aulos:ops:tasks:queue`, worker in lifespan.
- Dev blog generate/regenerate → **202** enqueue `dev_blog.generate`; sync mode for tests (`AULOS_TASK_QUEUE_SYNC`).
- API: `GET /v1/ops/tasks/dashboard`, `/tasks`, `/tasks/{id}`; dashboard aggregates mail + listening + ops.
- Ops UI: **Tasks** tab (`TaskQueuePanel`), Dev Blog panel polls task completion.
- Gates: `tests/test_task_queue.py`, `tests/test_dev_blog.py` (8 passed).

## 2026-07-27T10:15:00Z

- SPEC-017: Dev Blog **internal writing contract** — evidence-only, factual dev trace; no hype/emotion/external marketing.
- `dev_blog_contract.py`: SYSTEM_PROMPT rewrite + `validate_dev_blog_body()` soft lint; fake draft aligned.
- Promoted into SPEC-009, ops SPEC-002, REQ-002, `aulos-operating-defaults`, Ops UI lead copy.

## 2026-07-26T19:20:00Z

- Root cause: `merge_dossiers` called bare `dict(zh_hans)` when LLM/web returned prose/list →
  `ValueError: dictionary update sequence element #0 has length 1; 2 is required`
  (Mozart piano concerto guide=43 failed in `listening.synthesize`; same error in web_research).
- Fix: `coerce_dict()` + harden merge/parse/runtime/KB; gate `tests/test_salon_codex_merge.py`.

## 2026-07-26T19:10:00Z

- SPEC-013 delta: countable listening-chain plan (15 stages) seeded in `steps_json`; gateway emits live stage updates; SSE `progress` snapshots for reconnect.
- Robust recovery: client SSE reconnect + hydrate; `POST /{id}/retry` for failed/stale jobs; Atelier progress bar + Retry chain.
- Gates: `tests/test_listening_plan.py`, `tests/test_listening_jobs.py`; web `npm run build`.

## 2026-07-26T18:20:00Z

- Operating rule: every model-shape slice must close with dual-dialect `schema_patches` + PG verify (SQLite pilot ≠ production).
- Added `aulos_api.db.schema_patches`; HA/init apply on Postgres+SQLite. Migrated live PG SPEC-013 columns (`message`, `tags_json`, `favorited_at`, …).
- Gate: `tests/test_schema_patches.py`; promoted insight + `aulos-operating-defaults` section.

## 2026-07-26T18:15:00Z

- SPEC-013: durable listening-guide jobs (`queued`→`running`→`completed|failed`), Redis/`thread` worker (`listening_queue.py`), reconnect-safe `GET …/events`.
- Library: DELETE, list `q`/`status`/`published`/`favorited`/`tag`, favorite + tags.
- Legacy `/stream` and recompose/stream enqueue then attach to job events (no long-held DB session).
- Verify: `pytest tests/test_listening_jobs.py` + stream/recompose SSE green.

## 2026-07-26T17:20:00Z

- SPEC-012: per-run `chain_trace` (aulos.chain_trace/v1) in research_json for 复盘
- Milestones: discogs → identity → lock → rag → web → llm → skill.intake/synthesize → persist
- Auto deviations: composer/title drift, family_without_work_id
- Routes: owner `GET /v1/listening-guides/{id}/trace`, ops `GET /v1/ops/listening-guides/{id}/trace`
- Verify: `pytest tests/test_chain_trace.py` 4 passed

## 2026-07-26T17:10:00Z

- Discogs intent rewrite avoids `I'm listening to…` intake trap; Discogs title/composer always win over weak Catalog
- Companion fix in aulos-skills family composer gate (Mozart K.488 no longer inherits Beethoven cello pack)
- Verify: `pytest tests/test_discogs.py` 8 passed; live `/discogs #6280908` synthesize=`kb-rag` only

## 2026-07-26T17:00:00Z

- SPEC-008 delta: `suggest_discogs_releases` + authenticated `GET /v1/discogs/search` AJAX autocomplete
- Classical-first hit ranking; catno + free-text search; no full release fetch until compose
- Verify: `.venv/bin/pytest tests/test_discogs.py` 8 passed

## 2026-07-26T17:05:00Z

- SPEC-011: Redis mail queue `aulos:mail:queue` + background worker; live verify/reset async
- Fake mail stays sync; Mailgun probe stays sync; Redis fail → daemon thread fallback
- Ops `GET /v1/ops/mail/queue`; verify: `pytest tests/test_mail_queue.py` (+ auth/mailgun) 18 passed

## 2026-07-26T16:55:00Z

- SPEC-010: Salon Codex email craft for verify / reset / Mailgun probe (HTML + text)
- Tokens: stage `#0c1216`, parchment `#c9a66b`, Fraunces display; Mailgun sends `html`
- Verify: `pytest tests/test_email_templates.py tests/test_mailgun.py tests/test_auth.py` 14 passed

## 2026-07-26T16:50:00Z

- SPEC-002: `POST /v1/auth/forgot-password` + `POST /v1/auth/reset-password`; Mailgun `reset_password` mail
- Anti-enumeration; one-time `EmailToken` purpose=`reset_password`
- Verify: `pytest tests/test_auth.py` 7 passed

## 2026-07-26T16:30:00Z

- SPEC-009: `/v1/ops/dev-blog` list/get/generate; `dev_blog_posts` table; `services/dev_blog.py`
- Collect UTC-day git + harness excerpts; Ops LLM or fake template with product narrative headings
- Verify: `pytest tests/test_dev_blog.py` 5 passed offline

## 2026-07-25T19:50:00Z

- REVIEW-008 smoke `423-287-1`: was truncating to release 423; now catno search → Mozart/Horowitz
- Fixes: parse catno, Discogs search, exclude composer from performers, workish titles
- Verify: `test_discogs.py` 6 passed; live `resolve_discogs_message("/discogs #423-287-1")` SMOKE_OK

## 2026-07-25T19:40:00Z

- Root cause of “no Discogs token UI”: local-only; live OPS/API not redeployed
- Deployed host: OPS nav **Discogs** tab + `/v1/ops/discogs` (401 without auth = route live)

## 2026-07-25T19:35:00Z

- OPS GUI: dedicated **Integrations** tab for Discogs token (status + enable + save/clear); Overview link

## 2026-07-25T19:30:00Z

- OPS office: `/v1/ops/discogs` + LLM tab form to store Discogs personal user token (overrides env)

## 2026-07-25T19:20:00Z

- Renamed slash command `/discog` → `/discogs` (parser only accepts `/discogs`)

## 2026-07-25T19:15:00Z

- STORY-PACK-008 `/discogs`: REQ/SPEC/STORY/CKPT authored; id = Discogs **release** (master fallback)
- Implemented `services/discogs.py` + `parse_discogs_command`; wired `_run_chain_core` seed vinyl/interpretations
- Studio hint for `/discogs #release-id`; tests: `test_discogs.py` 4 passed; listening-guide regression green

## 2026-07-25T18:25:45Z

- Web research loop: thin RAG → Wikipedia/DDG (+ optional Brave) → LLM verify → KB upsert (user + global)
- Ops `/v1/ops/web-research` + LLM tab controls; query variants for opus-specific titles
- Verified: `tests/test_web_research.py` 5 passed; live Dvořák Dumky `rag_mode=no_match+web-research`, persisted docs 12/13, next search 6 hits

## 2026-07-25T17:22:35Z

- STORY-PACK-007 S2: `_rag_context` resolves Catalog work_id for knowledge-plane retrieve
- Client-side drop of mismatched `aulos_work_id` hits; `tests/test_knowledge_plane_rag.py` green

## 2026-07-26T01:15:00Z

- RAG aligned to Work Identity Catalog (REQ-006): seed identity cards; weak tokens from policy
- works_compatible respects work_id; identity_only cards never replace full dossiers

## 2026-07-26T00:55:00Z

- RAG identity gate: `bwv`/form words are weak tokens; soft-filter requires distinctive overlap
- Retrieve must not attach Goldberg `kb_dossier` to Bach cello suites / 大提琴无伴奏组曲
- SPEC-006 identity hard-gate + regression tests

## 2026-07-25T17:15:00Z

- Listening gateway delegates to AgentProxy.run_listening (no local iter_listening_chain)

## 2026-07-25T17:00:00Z

- Added ``aulos_api.timefmt.to_utc_iso``; listening/ops/mailgun wire UTC ``Z``; tests/test_timefmt.py

## 2026-07-25T14:53:12Z

- Research KB + vector RAG: knowledge_documents/chunks, embeddings ops settings, lexical fallback, corpus seed
- Recompose/update-publish APIs; by-share ownership; studio + /g owner toolbar
- SPEC-006; listening tests for KB search + recompose slug stability


## 2026-07-25T11:52:22Z

- STORY-002..005 auth MVP: users/roles, register/verify/login, Mailgun config (fakeable), superadmin ops gate
- SQLite + JWT + bcrypt; bootstrap superadmin via env
- aulos-web register/login/verify UI; aulos-ops superadmin + Mailgun settings
- pytest auth suite green; public smoke on aulos.purezen.ai / aulos-ops.purezen.ai


## 2026-07-25T11:07:43Z

- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`
- no execution history recorded yet

## 2026-07-25T12:21:57Z

- Added ops-managed LLM providers (DeepSeek + Grok) with GET/PUT/test; chat uses live provider when ready.
- Verified: pytest 20 passed; ops UI LLM tab deployed.

## 2026-07-25T12:55:17Z

- Shipped listening-guide MVP (REQ-003/SPEC-003): width+depth research workflow, HTML guide, observable steps, web studio UI.
- Verified: pytest 22 passed; Goldberg smoke guide created; aulos-web redeployed.

## 2026-07-25T13:23:08Z

- Longrun 1–4 done: SkillRuntime drives listening guides; skill_versions persisted; MCP skills.list/run; ops Skills tab; web shows skill ids.
- Verified: skills 5 / api 22 pytest; live Goldberg probe score=10; guide steps cite aulos-listening-*.

## 2026-07-25T13:34:45Z

- Closed residual 1–4: ops Disable now skips skill steps at runtime; SSE `/v1/listening-guides/stream`; web live chain; serve.py streams event-stream.
- Verified: skills 7 / api 24 pytest; SSE smoke on :5090 and proxy :5091.
