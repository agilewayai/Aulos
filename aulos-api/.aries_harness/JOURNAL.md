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
content_fingerprint: "sha256:9f38e320ad76488fd91218c2b67e70ad46150b13ffcd417bafcd61493248720f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-08-02T10:02:45Z

- Deployed gateway Slice H production code with `bash deploy/aulos-ctl.sh
  deploy`; build/restart/ingress/local-public smoke completed successfully.
- Post-deploy `smoke` and `status` stayed green: `aulos-api`, `aulos-web`,
  `aulos-ops`, and `aulos-knowledge` active; API `/health` reports PostgreSQL
  primary OK and failover OK.
- Production PostgreSQL guide #60 trace confirms gateway `g.program` budget work
  addresses the real slow stage; `ambient_ok=false` remains a fail-closed product
  gate and was not bypassed.

## 2026-08-02T10:15:00Z

- **Review Critics → AI Code Mirror (Codex):** agent `_ops_llm_complete(role=review)`
  now uses `invoke_provider` (Responses wire), not chat-only Completions.
  Ops draft/review roles are canonical — env role overrides require
  `AULOS_LLM_ROLE_ENV_OVERRIDE=1`. Verify: `tests/test_ops_llm.py` 10 passed;
  agent `tests/test_ops_llm_critic.py` 3 passed.

## 2026-08-02T09:50:00Z

- **LLM provider: AI Code Mirror (Codex Responses relay):** Ops slot
  `aicodemirror` — default model `gpt-5.5`, base
  `https://api.aicodemirror.ai/api/codex/backend-api/codex`, `wire_api=responses`,
  reasoning `xhigh`. Key via Ops or `AICODEMIRROR_API_KEY` in host.env.
  Invoke path uses Responses API (`/responses`), not Chat Completions.
  Verify: `pytest tests/test_ops_llm.py` 8 passed.

## 2026-08-02T09:44:23Z

- SPEC-034 Slice H gateway fix implemented from production PostgreSQL guide #60
  RCA: `g.program` was the long stage, not `g.rag`.
- API fix: `web.research` program-deepen config now defaults to fast/budgeted
  mode; fast raw-web path bypasses Agent Reach/Jina and LLM verify while
  preserving raw evidence and timing metadata.
- Ready multi-work fast mode skips album-level `g.llm`; full deepen remains
  explicit configuration.
- Tests: `tests/test_web_research_partial.py` green (4 passed).

## 2026-08-02T07:24:00Z

- **Production deploy sync:** root `bash deploy/aulos-ctl.sh deploy` published
  the current dirty tree, including SPEC-034 Slice F API gateway/persist gates.
  `aulos-api.service` restarted at `2026-08-02 15:18:38 CST` and remained active.
- Verify: root `doctor` passed; deploy test suite -> 5 passed; root `status`
  showed API/Web/Ops/Knowledge active; root `smoke` passed local + public health.
  API logs showed db HA, mail, listening, and ops task workers started with Redis
  OK plus HTTP 200 health/app paths.
- Central deploy evidence:
  `../aulos-skills/.aries_harness/runs/deployments/DEPLOY-2026-08-02-spec-034-slice-g-production.md`.
  Residual: guide #59 live recompose not run.

## 2026-08-02T06:21:15Z

- **SPEC-034 Slice F consumer / guide #59:** hot Postgres latest guide remained
  `#59` (created `2026-08-02T05:29:38Z`), with `eval_pass=false` but
  `status=completed`. RCA: API credit parse first classified release artists as
  performers when no explicit composer role existed, blocking structure-level
  composer inference; gateway `g.program` used the global empty composer instead
  of per-work composers; persist accepted failed eval/ambient/process gates as
  completed.
- Fix: Discogs core parsing now prefers explicit performer-role names over
  blanket top-level-artist performers, allowing structure inference for
  Hummel/Weber/Haydn class releases. Gateway program iterations carry
  per-work composer into web research + LLM enrich. `_apply_report_to_row`
  fail-closes on `eval_pass=false`, process hard-fail, review/decontam,
  ambient gate, or structure hard-fails; failed reports keep HTML/steps/research
  for review but are not KB-indexed. Guide publish + diary-guide publish require
  `status=completed` and non-empty HTML.
- Verify: `PYTHONPATH=. .venv/bin/pytest -q tests/test_discogs.py` -> 12 passed;
  `PYTHONPATH=. .venv/bin/pytest -q tests/test_listening_jobs.py
  tests/test_diary_guides.py` -> 9 passed. Broader `test_listening_guide.py`
  still has two legacy step-id expectation failures (`intake`/`eval` vs current
  `listening.*`/`g.*`) unrelated to this slice.

## 2026-08-01T23:10:00Z

- **META-001 v9 consumer (guide #57):** gateway program loop uses
  `search_query` (catalog-first); on LLM enrich fail keeps `web_dossier` raw floor.
  `verify_sources_to_dossier` degrades to `web_search_raw` on LLM error (no empty
  `{}`). Persist partial raw dossiers. Verify: `test_web_verify_degrade` green.
  Live ops: DeepSeek key 401 — operator must rotate; degrade path unblocks deepen.

## 2026-08-01T22:55:00Z

- **SPEC-034Δ program deepen loop (gateway):** after `g.rag`, multi-work
  `structure_ready` runs `g.program` — per program work forced `cold_fill` web
  (keep snippets on verify_failed) + LLM enrich; album `g.web` skips as
  `delegated_to_program_loop`. Plan stage added; iterations travel on
  research context / kb_dossier into Agent synthesize.
- Verify: `test_web_research_partial` + `test_listening_plan` green.

## 2026-08-01T22:40:00Z

- **SPEC-034 Slice B/C (consumer):** gateway stores `release_structure` on
  kb_dossier + research_json; `discogs.structure` chain milestone; discogs
  context carries program map into Agent.
- Verify: `tests/test_discogs.py` green with structure emit.

## 2026-08-01T22:20:00Z

- **SPEC-034 Slice A (consumer):** `analyze_discogs_release` + `build_diary_snapshot`
  emit `release_structure` (program map / structure_ready / expansion_plan) via
  `aulos_skills.release_structure`. META-001 §4.1 covenant owned in aulos-skills.
- Verify: `tests/test_discogs.py` 11 passed.

## 2026-08-01T22:10:00Z

- **Regen pollution loop:** targeted revise / review reused masked polluted
  `corpus_dossier` (lock BWV kept while ZH/Op. foreign remained); Rule-1 betrayal
  previously required *no* lock numbers preserved. Fix: foreign catalog in craft
  chambers betrays even when lock numbers are force-copied; RAG drops betraying
  docs from hits; upsert refuses polluted indexes; recompose clears prior corpus +
  purges same-guide/same-composer betraying KB; diary/targeted revise escalates to
  full recompose when polluted. Tests: identity_lock + knowledge_retrieve +
  `test_regen_pollution_gate` green.

## 2026-08-01T21:55:00Z

- **RAG foreign-dossier bleed (Hindemith→Bach class):** root cause was
  `works_compatible` treating Discogs template glue (`discogs`/`performers`/`release`)
  as distinctive identity, plus soft-filter substring `in ⊂ Hindemith`, after a
  prior pressing was indexed with swapped composer/title. Fix: expand
  `weak_tokens.yaml` packaging/glue list; token-boundary soft-filter; locked
  composer gate; refuse `kb_dossier` when `dossier_betrays_identity_lock` (catches
  self-poisoned Bach-labeled rows still carrying Op.11 chambers). Tests:
  `tests/test_knowledge_retrieve.py` green.

## 2026-08-01T21:45:00Z

- **SPEC-033 (skills) intake:** `_guess_work_title` keeps program-level Discogs
  titles when ≥2 catalog numbers are present (no single-track collapse). Test:
  `test_multi_catalog_release_keeps_program_title`.

## 2026-08-01T21:00:00Z

- **SPEC-031:** `POST …/promote-production` graduates any staged promote_candidate
  via generic Catalog+craft pipeline (tmp-rooted in tests).

## 2026-08-01T20:40:00Z

- **SPEC-030:** `GET …/promote-candidates`, `POST …/{id}/promote-stage`; trace +
  scorecard summaries expose promote/product asset signals.

## 2026-08-01T20:25:00Z

- **SPEC-029 companion:** `_research_payload` persists `promote_candidate` +
  `facet_classification` when synthesize emits unknown-case thicken.

## 2026-08-01T20:05:00Z

- **SPEC-028 companion:** `ensure_catalog_composer_dossiers` +
  `POST /v1/ops/knowledge/composers/ensure-dossiers` (dry_run supported).

## 2026-08-01T19:50:00Z

- **SPEC-026 companion:** `dossier_is_thin` + `enqueue_composer_dossier_build_sync`;
  listening_guide enqueues build when composer dossier is thin (non-blocking).

## 2026-08-01T19:32:00Z

- **SPEC-025 companion:** `fetch_composer_dossier_sync` + listening thicken bag;
  `_research_payload` persists `product_scorecard`; Mendelssohn knowledge dossier
  built via admin `build-dossier` (job 136/137). Guide #50 product **100% strong**.

## 2026-08-01T19:10:00Z

- **SPEC-024 companion:** Discogs identity lock uses Work Resolver; keeps Catalog
  `work_id` when packaging-cleaned titles match; `work_hint` uses em-dash.
- Guide #50 full-chain regen → eval **10 / pass**.


## 2026-08-01T18:45:00Z

- **REQ-013 / SPEC-023 (skills) companion:** Discogs `_guess_work_title` now runs
  `clean_packaging_work_title` so multi-language release dumps do not become IntentLock.
- Verify: `tests/test_discogs.py` green.


## 2026-08-01T18:05:00Z

- **SPEC-022Δ:** Diary guide revise uses `enqueue_targeted_revise_guide` /
  `kind=targeted_revise` (chamber patch from notes + research snapshot), not full
  listening chain. Queue worker handles targeted path.


## 2026-08-01T17:35:00Z

- **Ambient fallback OPS:** `listening.ambient_fallback_mode` (`embed`|`stream`) in
  `system_settings`; routes `/v1/ops/ambient-fallback`; inject into listening compose
  via AgentProxy. Tests: `tests/test_ambient_fallback.py` (2).


## 2026-08-01T17:20:00Z

- **DB pool + HA probe isolation:** Postgres QueuePool defaults `pool_size=20` /
  `max_overflow=40` (env-tunable). HA `probe()` uses dedicated NullPool with
  `render_as_string(hide_password=False)` / settings URL (avoid `***` auth false
  negatives). Require 3 consecutive probe failures before failover.
  Tests: `tests/test_db_ha.py` 3 passed; live `/health` primary_ok after restart.

## 2026-08-01T15:50:00Z

- **Ghost pending steps:** coalesce short agent ids onto listening.* placeholders
  on read/persist; heal completed guides in PG (guide #48 21/31 -> 18/18).
- Verify: pytest tests/test_listening_plan.py (8 passed).


## 2026-08-01T15:30:00Z

- **SPEC-013 progress count fidelity:** canonicalize skill short ids (route to listening.route);
  progress_counts exposes completed/skipped/failed; review milestones visible but non-countable.
- Verify: pytest tests/test_listening_plan.py (7 passed).

## 2026-08-01T11:34:00Z

- **REQ-011 / SPEC-021Δ:** Diary guide review lifecycle — `review_notes` + `revised_at` on
  `diary_guide_links`; revise (notes → `enqueue_recompose_guide` → queued), unpublish,
  dismiss-after-unpublish, delete link (hard-delete exclusive unpublished guide).
  Payload adds derived `actions` flags. Web: 审阅意见 + status-aware buttons.
- Verify: `pytest tests/test_diary_guides.py` (3 passed); `aulos-web` `npm run build` green.

## 2026-08-01T18:55:00Z

- SPEC-019: `GET /v1/ops/listening-guides/scorecards`; guide GET/trace/research_json carry `process_scorecard`; diary light payload includes scorecard.
- Verify: `tests/test_process_scorecard_api.py` passed.

## 2026-08-01T18:40:00Z

- SPEC-018: OPS `listening.review_llm` SystemSetting + `/v1/ops/listening-review`; gateway seeds `review_llm_enabled` into agent; research_json/chain_trace carry `intent_lock` + `review_events`.
- Verify: `tests/test_listening_review.py` + chain_trace **5 passed**.

## 2026-08-01T11:05:00Z

- Guide #47 Requiem drift: LLM prompt identity lock + `_dossier_betrays_lock` discard; Discogs vs Catalog `_titles_compatible` (K.488 token overlap) so work_id is not cleared by album chrome.
- Verify: helper smoke; skills `test_mozart_requiem_drift`.

## 2026-08-01T10:45:00Z

- META-001 §3.5: `_parse_release_core` unifies Discogs credit/id parse for `analyze_discogs_release` + `build_diary_snapshot` (ensembles no longer analyze-only gap); `share_slug.new_share_slug` shared by guide + diary.
- Verify: `pytest tests/test_discogs.py tests/test_listening_diary.py` (11 passed).

## 2026-08-01T08:40:00Z

- **SPEC-021 / STORY S6:** Diary → 聆乐导赏 queue (listening_queue) → author review → publish
  onto blog. Routes: `POST …/guides`, `GET guide-tasks`, publish/dismiss/ack. Web: generate CTA,
  queue banner, review panel; plaza shows published guides. Gate: `test_diary_guides.py`.

## 2026-08-01T07:45:00Z

- **REQ-010 / SPEC-019/020 longrun S1–S5:** Listening diary + 爱乐广场 SNS.
  - Discogs `build_diary_snapshot`; draft CRUD; publish/plaza/follow/like/comment.
  - Tables: listening_diary_posts, diary_guide_links (reserve), user_follows, likes, comments.
  - Web: product nav 广场 / 聆乐 / 导赏; My Diary create from Discogs; Plaza feed+following.
  - Gates: `pytest tests/test_listening_diary.py` 2 passed; `aulos-web` `npm run build` green.
  - Next (S6): diary → guide attach by aspect.

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
