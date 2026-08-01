---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "journal"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:05Z"
content_fingerprint: "sha256:d52befe0aec5f1c942d5a3f234981d5f01db96a47abdddfb42c0d6ba05f09c8a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-08-01T21:50:00Z

- **REQ-022 / SPEC-032 Identity freeze + Catalog/facet hardening (anti-case):**
  Probe class from multi-Köchel piano-sonata pressing (Eschenbach⊂bach, KV prefix
  false ties, German Sonaten → chamber-generic, promote poison slug). Shipped:
  `text_match.alias_in_text` word boundaries; IntentLock composer wins in synthesize;
  Catalog scoring rejects bare `kv`/`op` tokens + `multi_work` for unmatched multi-numbers;
  FacetClassifier `solo-piano-sonata` + German/rondo tokens (duo requires cello);
  form_lock `solo_keyboard` (duo suppresses solo); promote refuses drift/hard-fail;
  ProductScorecard `product_composer_drift`; packaging peel no longer eats form nouns;
  ambient playlist mode preserved under catalog-ref. Verify: `pytest tests/` **157 passed**.

## 2026-08-01T21:30:00Z

- **Mechanism tour:** wrote `.aries_harness/docs/SYSTEM_MECHANISM_TOUR.md` — fleet topology,
  atelier chain, identity law, thicken engine vs accelerators, promote graduation, dual
  scorecards, invariants. Lens = system/mechanism only (post-compression).

## 2026-08-01T21:15:00Z

- **Compression — delete case/temporary localize logic:** Removed all 10 hand-authored
  craft YAML packs; craft is promote-pipeline only. Stripped case marker lists
  (Bernstein H1, K.488 hints, Op.69/Fournier scrub, rival-composer maps, beethoven.jpg
  URL fingerprint, Mendelssohn-only surname bleed, goldberg-as-form-token, chamber-generic
  duplicate scaffold). External review aliens come from `form_lock_groups.yaml` only.
- Verify: 67 skills + promote API tests green.

## 2026-08-01T21:00:00Z

- **REQ-021 / SPEC-031 Dimensional promote (anti-case):** Facet voices
  `(instruments × forms × era)` thicken any unknown title; generic
  stage→Catalog stub→production craft pipeline. META-001 v6 encodes: Catalog/craft
  are accelerators; engine is dimensional — tests require ≥2 unrelated identities.
- Verify: `tests/test_dimensional_promote.py`, `test_promote_production_api.py`.

## 2026-08-01T20:40:00Z

- **REQ-020 / SPEC-030 Promote staging + ops surface:** Operator can stage
  `promote_candidate` → `craft/staging/{id}.yaml` (not production craft/). API
  list/stage endpoints; Guide quality panel Stage action; FacetClassifier tokens
  for prelude/etude/ballade/impromptu/fantasy/quartet.
- Verify: `tests/test_promote_staging.py`, `aulos-api/tests/test_promote_stage_api.py`.

## 2026-08-01T20:25:00Z

- **REQ-019 / SPEC-029 Unknown-Case Thicken Loop v1:** FacetClassifier → archetype
  floor (reuse family pack or built-in `chamber-generic`) → promote_candidate dry-run.
  Synthesize no longer depends on Catalog/craft YAML for unknown Discogs/NLP titles;
  `archetype:{id}` replaces bare `generic-scaffold` when confidence ≥ 0.4. API persists
  `promote_candidate` + `facet_classification` in `research_json`.
- Verify: `tests/test_unknown_case_thicken.py` (6) + thicken regressions green.

## 2026-08-01T20:05:00Z

- **REQ-018 / SPEC-028 Catalog craft + fleet dossier:** Craft YAML for all 10 Catalog
  works; scrub no longer wipes craft/catalog-floor theses that name conflict works to
  refuse them; `ensure_catalog_composer_dossiers` + ops
  `POST /v1/ops/knowledge/composers/ensure-dossiers`; live enqueue for thin Dvořák.
- Verify: `tests/test_catalog_craft_coverage.py`, `tests/test_ensure_composer_dossiers.py`.

## 2026-08-01T19:55:00Z

- **REQ-017 / SPEC-027 genre family coverage:** Added `piano-concerto`, `sacred-requiem`,
  `symphony-orchestra`, `piano-trio` bilingual family packs; every Catalog work now has
  registered `family_id`; synthesize prepends Catalog family lock; catalog craft floor
  auto-loads family by id; Mahler + Dvořák composer cards in synthesize index.
- Verify: `tests/test_family_coverage.py` (14 related green with systemic/craft).

## 2026-08-01T19:50:00Z

- **REQ-016 / SPEC-026 systemic cold-path thicken:** Catalog craft floor binds any
  Catalog `work_id` + family into work-specific Salon chambers (no hand YAML required);
  explicit craft pack still wins. Thin knowledge dossier after identity lock
  fire-and-forget enqueues `build-dossier`. ProductScorecard gains `asset_depth`;
  identity-resolved family-only shelves capped ≤ solid / fail if asset empty.
- Verify: `tests/test_systemic_cold_thicken.py` (+ product/craft regressions).

## 2026-08-01T19:32:00Z

- **REQ-015 / SPEC-025 knowledge thicken + ProductScorecard:** Knowledge-plane
  composer dossier → Salon chambers (`knowledge_thicken`); Catalog work craft packs
  (`assets/craft/{work_id}.yaml`) merge after family and re-assert EN/ZH theses over
  LLM poetic drift; ProductScorecard dual-track (`eval_pass` ← product band; process
  stays diagnostic); API persists `product_scorecard` in `research_json`.
- **Alien marker bounds:** bare `988` no longer hard-fails inside year `1988`
  (`marker_in_text` digit boundaries in decontam / process / adversarial).
- **Guide #50:** process **76.1% hard_fail** (false `988`) → **81.2% solid no hard_fail**;
  product **100% strong**; eval **10 / pass**; synthesize
  `…+craft:mendelssohn.lieder-ohne-worte+…+knowledge-plane`; Mendelssohn knowledge
  dossier built (portrait + timeline); craft ZH「歌唱房间」pinned in HTML.
- Verify: `tests/test_knowledge_product_score.py`, `tests/test_marker_boundaries.py`,
  `tests/test_craft_raise.py`.

## 2026-08-01T19:10:00Z

- **REQ-014 / SPEC-024 craft raise:** Work Resolver (Discogs packaging → Catalog
  `work_id`/`family_id`); chamber contracts (EN floors + ZH parity) in eval; cold
  thicken via registered `lyric-piano-miniatures` + Mendelssohn composer card; family
  forms-hit so Songs Without Words is not refused as foreign for missing "piano" token;
  atelier eval accepts double-quoted HTML ids; API Discogs lock keeps Catalog when
  resolver matches.
- **Guide #50:** original eval **7 fail** / dishonest v2 91.7% → hygiene **9 pass** →
  craft raise **10 pass**; portrait/genesis/sound/interpretations filled; EN+ZH theses
  aligned; `work_id=mendelssohn.lieder-ohne-worte`.
- Verify: `tests/test_craft_raise.py` + runtime/identity hygiene regressions.


## 2026-08-01T18:45:00Z

- **REQ-013 / SPEC-023 product-prose hygiene (systemic):** Root-cause classes from
  Mendelssohn《无词歌》guide #50 — packaging IntentLock, CRITIQUE LOCK in thesis,
  CJK-on-EN, large-scale form placeholder, review empty-body hallucination, gameable
  scorecards. Shipped `prose_hygiene` + hooks in Discogs / synthesize / compose /
  revise_repair / external_review / scan_hard_flaws; catalog Mendelssohn +
  `lyric-piano-miniatures` family; RAG packaging-dump filter.
- **Follow-up from deep RCA:** intake dash-regex no longer splits hyphenated surnames;
  composer-name strip prefers longer aliases; Discogs `work_hint` uses `Composer — Title`;
  enrichment JSON no longer pasted into width bullets; review_targets map title/process
  codes to `work_title`; bilingual score requires craft parity; identity score hard-fails
  packaging titles.
- **Regen #50:** eval_score **7→9** (fail→pass); product: clean title, bilingual EN/ZH
  theses aligned, no process locks, lyric miniature form. Process scorecard now honest
  (~70.8%, 0 hard) vs prior dishonest v2 91.7% with locks still in HTML.
- Verify: `tests/test_prose_hygiene.py` + `tests/test_external_review_hygiene.py` +
  `test_intake_i18n` surname case; `aulos-api` `tests/test_discogs.py`.


## 2026-08-01T18:00:00Z

- **SPEC-022Δ targeted revise:** semantic `review_targets` (expert codes + human notes)
  → chamber patch via `targeted_revise` (no default full compose); `generation_rounds` v2
  with frozen `draft_v1`, latest report/v2, `revision_history`; diary revise enqueues
  `kind=targeted_revise`; Studio panel shows iteration history + score deltas.
- Verify: `test_review_targets` + `test_targeted_revise` + `test_external_review_round`;
  diary revise lifecycle.


## 2026-08-01T17:30:00Z

- **REQ-005 / SPEC-006Δ:** Disable ambient-library related/defaults rotation; scrub
  peer/stand-in curated ambient; OPS `listening.ambient_fallback_mode` (`embed` default |
  `stream` yt-dlp); `ambient_video` + embed DOM (`v2-embed`); eval ambient gate softened
  (missing player is soft score, not hard-fail alone).
- Verify: `tests/test_ambient_agent.py` + `test_ambient_video.py` + eval soft note (15);
  `aulos-api` `tests/test_ambient_fallback.py` (2); Mozart Moonlight stand-in → `{}`.


## 2026-08-01T16:20:00Z

- **SPEC-022 revise repair:** apply_review_repairs + optional LLM proofread; rescore
  draft_v1 with hard-flaw penalties; draft_v2 scored on remaining flaws so dual
  scorecards diverge (comparison tracks hard_flaws delta).
- Verify: pytest tests/test_external_review_round.py (6 passed).


## 2026-08-01T16:00:00Z

- **SPEC-022Δ:** External Review Agent perspective = music guide + analysis expert;
  hard-flaw findings only (no web_catalog_weak source hunt). LLM expert completer
  attached in agent; UI shows 专家视角 / 硬伤修复指令.
- Verify: pytest tests/test_external_review_round.py.


## 2026-08-01T12:15:00Z

- **Deploy + regen:** `aulos-ctl deploy` smoke green; Guide #48 recomposed with
  `generation_rounds` (v1/review/v2) — comparison 94.4% / 94.4% (tie), review
  verdict PASS (1 low: web_catalog_weak). Live web ships「双稿与联网 Review」panel.

## 2026-08-01T12:07:00Z

- **REQ-012 / SPEC-022:** Post-compose networked External Review Agent round —
  playbook `compose → external_review → revise → eval`; API injects open-web
  `external_review_sources`; persists `generation_rounds` (draft_v1 / review_report /
  draft_v2 / comparison); Studio+diary UI tabs for 初稿/报告/修订稿 + dual scores.
- Verify: `tests/test_external_review_round.py` + identity/process **13+**; agent listening
  tests; `aulos-web` build green.

## 2026-08-01T11:47:00Z

- **Guide #48 root-cause (Mozart K.488 / Horowitz):** three drift classes fixed via SPEC-009Δ
  + SPEC-019 self-improvement — not symptom patches.
  1. H1「伯恩斯坦谈莫扎特」: `guide_render` video loop shadowed `title` → last appreciation
     video overwrote work H1.
  2. Mozart portrait = Beethoven.jpg: no Mozart composer card + no portrait↔composer gate;
     KB/polluted layer supplied Beethoven cello-room caption.
  3. Beethoven cello Op.69 chambers: KB carried `dossier_id=family:duo-cello-piano` while
     `synthesize_source` lacked `family:` — prior decontam only checked source string; shared
     `piano` token masked instrument-miss.
- **Class fix:** `identity_hygiene.py` (portrait betrayal + composer-scoped/strong-instrument
  foreign family); synthesize refuses polluted KB; scrub cleanses `historical_stature.reasons`
  + portrait; decontam/review + scorecard identity hard_fail → `critique_corrections` rework.
  Mozart composer card added; K.488 catalog conflict_markers expanded.
- Verify: `tests/test_identity_hygiene.py` + process/adversarial/runtime/media **39 passed**.

## 2026-08-01T18:55:00Z

- **SPEC-019 / REQ-009:** Listening process scorecard — `process_scorecard.py` NodeScorecard per skill node + ProcessScorecard rollup at eval; Atelier card; Ops Guide quality board; research_json/chain_trace persistence. Legacy `eval_score`/`pass` unchanged.
- Verify: skills `test_process_scorecard` + adversarial **12 passed**; API scorecard list/trace; web+ops `npm run build` green.

## 2026-08-01T18:40:00Z

- **SPEC-018 / ADR-005 / REQ-008:** Hybrid adversarial process review for listening atelier.
  - Intake freezes `intent_lock` (Discogs/Catalog/diary truth); later nodes cannot overwrite.
  - Unified `_adversarial_review_gate`: deterministic ReviewReport every enrich node; LLM/intent Critic after synthesize+compose; `critique_corrections` rework ≤1; eval soft-fail on `review_failed`.
  - Atelier emits `review-*` milestones; chain_trace / research_json expose review events.
  - OPS `listening.review_llm` switch; agent re-attaches Critic completer per tool call (JSON-safe).
- Verify: `tests/test_adversarial_review.py` + mozart/identity_lock **14 passed**.

## 2026-08-01T11:20:00Z

- Operator challenge: prior Requiem fix still smelled case-specific (K.488 hardcode).
- **Class gate:** `identity_lock.py` + `policies/form_lock_groups.yaml` — catalog-number lock + form-family aliens (concerto↔sacred_mass, etc.) with **zero per-work Python branches**; intake merges lock aliens into conflict_markers; synthesize drops betraying LLM layers; API betrayal uses the same module; SPEC-008 acceptance updated.
- Verify: `tests/test_identity_lock.py` (Beethoven/Brahms/generic) + mozart drift + identity/runtime **31 passed**.

## 2026-08-01T11:05:00Z

- **Root cause (guide #47):** Horowitz DG Mozart pressing (K.488 concerto + K.333) drifted to Requiem/末日经.
  Drift chain: no Mozart Catalog card → identity unknown → LLM free-associated Horowitz+Mozart → Requiem transcription meme;
  Discogs title vs Catalog substring check could also drop a correct work_id; compose decontam scrubbed dossier but left stale `guide_html`.
- **Class fix:** Catalog Mozart + K.488 + Requiem (bidirectional conflict markers); form-lock aliens in `decontam`; intake `Composers:` line; LLM identity lock + betrayal reject; `_titles_compatible`; compose re-render + HTML marker scrub.
- Verify: `pytest tests/test_mozart_requiem_drift.py` (+ identity/runtime) green.

## 2026-08-01T10:40:00Z

- META-001 §3.5: extract `aulos_skills.html_bits` (`point_text(s)`, `html_li`, `html_p`); `guide_render` wraps them; delete unused legacy `render_guide_html` + local `_li`/`_p`/`_point_*` from `runtime.py` (compose already uses bilingual renderer).
- Verify: `pytest tests/test_html_bits.py` + `tests/test_runtime.py` green.

## 2026-08-01T10:25:00Z

- META-001 → **v5**: added §3.5 DRY (no copy-paste product code); strengthened §3.1/§3.2 against duplicated implementations. Spurred by Studio vs diary atelier fork → shared `AtelierTrail`.

## 2026-08-01T10:15:00Z

- Fix Agent atelier crash: LLM/KB `width_points`/`depth_points` may be dicts; `_detail_from_outputs` used `"; ".join(points)` → `sequence item 0: expected str instance, dict found`. Coerce via `_point_text(s)`; harden rag_hits + eval earish. Triggered by diary Mozart Horowitz K.488 guide #47.

## 2026-08-01T06:35:00Z

- Honeycomb closeout after META-001 §3.4 Meta Play Simple promotion + knowledge/ops console ship.

## 2026-07-27T16:40:00Z

- **META-001 v4 §3.4 Product interaction — Meta Play Simple:** human nouns first, progressive disclosure,
  curated seed networks; promoted from Explore UX (composer A–Z / Famous / portraits).

## 2026-07-27T11:20:00Z

- Promoted **Authority Source Registry** into META-001 §4 + insights (aulos-knowledge REQ-008 / ADR-006 / REG-SRC-001).

## 2026-07-27T10:50:00Z

- **META-001 v2** — promoted insights →纲领: data-over-heuristics, multi-stage validate, harness forced + facility, deploy-in-delivery, LLM coerce, hard-fail gates, architecture boundaries (agent / knowledge / identity→RAG).
- `docs/insights.md` entries tagged `↑ META-001 §…` or `→ operating-defaults/SPEC` (domain stays out of META).

## 2026-07-27T10:45:00Z

- **META-001** Meta Principles (纲领层): root-cause thinking, asset synchronization, engineering craft / anti-smells.
- Registered in REG-001; MetaDefineLayer manifest; promoted to workspace `AGENTS.md`, `CLAUDE.md`, `aulos-operating-defaults`.

## 2026-07-27T09:45:00Z

- Fleet DevOps control plane:
  - `deploy/aulos-ctl.sh` — unified commands: `deploy`, `build`, `restart`, `status`, `smoke`, `logs`, `doctor`, `secrets {init|check}`, `units install`, `ingress apply`, `test`.
  - Shared libs under `deploy/lib/`; `start-host.sh` → thin `aulos-ctl deploy` wrapper.
  - Canonical runbook `deploy/OPS.md` (architecture, secrets, gates, rollback).
  - Promoted into `AGENTS.md`, `README.md`, `CLAUDE.md`, `aulos-operating-defaults/SKILL.md`, `deploy/README.md`.
- Verify: `aulos-ctl doctor`, `test` (5 passed), `smoke` all green.

## 2026-07-27T09:30:00Z

- AUDIT-009 continuation — F2 / F10 / F11 (F1 deferred per operator):
  - F11: `ADR-008-plaintext-systemsetting-secrets-sprint1.md` accepts Sprint-1 plaintext secrets with compensating controls.
  - F2: `SPEC-015` guide HTML security; `guide_html_security.sanitize_guide_html` + public CSP tests; web `guideHtml.ts` sandbox selftest (no `allow-same-origin`).
  - F10: `SPEC-016` seams — extracted `guide_html_security.py`, `ops_mail.py`, `ops_integrations.py`, `SkillsPanel.tsx`, `guideHtml.ts`. Line cuts: `listening.py` 801→522, `ops.py` 971→621, ops `App.tsx` 1677→1491.
- Verify: API `94 passed`; web/ops builds + ops lint green; `guideHtml.selftest` ok.

## 2026-07-27T09:10:00Z

- AUDIT-009 continuation slice — F3 + F2 follow-up:
  - SPEC-014: login sets HttpOnly `aulos_session`; logout clears it; `get_current_user` accepts cookie or bearer.
  - `aulos-web` / `aulos-ops`: `credentials: 'include'`, removed `localStorage` JWT storage.
  - Added `tests/test_guide_security.py` for public guide CSP/security headers.
  - Test helper `clear_session()` for cookie-aware unauth assertions.
- Residual: operator secret rotation (F1); F10 module splits; optional Playwright F2 stretch.

## 2026-07-27T08:52:00Z

- AUDIT-009 remediation slice (security + verification):
  - F1: removed tracked JWT/bootstrap defaults from `deploy/systemd/user/aulos-api.service`; `deploy/start-host.sh` now requires non-default secrets in `.run/host.env` including `AULOS_KNOWLEDGE_ADMIN_TOKEN`.
  - F4/F8/F9: API full suite green (`89 passed`); worker shutdown/join + `tests/conftest.py` isolation; web-research freshness uses provenance only (not `doc.updated_at`).
  - F5: `aulos-knowledge` `/v1/admin/*` requires bearer token; API proxy forwards `AULOS_KNOWLEDGE_ADMIN_TOKEN`.
  - F2/F7: guide iframe drops `allow-same-origin`; public guide CSP + security headers; deploy static host headers.
  - F6/F12: `aulos-knowledge` in root inventory + `AGENTS.md`/`MISSION`/`EVAL`; ops lint warning-free.
- Residual: F3 HttpOnly session auth; operator must rotate live secrets.

## 2026-07-27T08:36:49Z

- Completed workspace-wide architecture/code review as `AUDIT-009`.
- Verdict: not ready for production signoff; F1 fixed deploy JWT/bootstrap defaults, F2/F3 guide HTML + browser token exposure, F4 red API suite, and F5 knowledge-plane direct admin auth are the priority blockers.
- Verification snapshot: API full suite red (`87 passed, 1 failed, 1 error`); skills/agent/MCP/knowledge/deploy tests and web/ops builds passed; ops lint still has one hook dependency warning.

## 2026-07-26T19:25:00Z

- Root-cause guide #44 (Brahms Violin Concerto Op.77): `duo-cello-piano` unlocked on
  composer `brahms` alone (score≥2, zero instrument/form evidence) → Beethoven cello
  chambers + Bach Suite I ambient.
- SPEC-009 / REQ-007: family evidence gate + per-node decontam validate/rework.
- Ambient related packs: foreign-composer / empty-composers peer gates; defaults skip
  foreign composer titles when shelf composer is known.
- Gate: `test_brahms_violin_concerto_not_duo_cello_family` + runtime/ambient/identity 29 passed.

## 2026-07-26T19:20:00Z

- Harden `salon_codex.merge_dossiers` / `coerce_dict` against LLM `zh_hans` prose/list (Mozart piano concerto crash: dictionary update sequence element).
- Gate: `tests/test_salon_codex_merge.py` + runtime Mozart path; insight promoted.

## 2026-07-26T19:05:00Z

- Media shelf: appreciation videos + interpretation YouTube rows now also get 哔哩哔哩 search links (`search.bilibili.com`).
- `media_search.enrich_*` derives keyword from existing YouTube `search_query` or title; renderer shows YouTube · 哔哩哔哩.
- SPEC-003 / listening-width skill + LLM dossier prompt updated; gate `tests/test_media_search.py`.

## 2026-07-26T17:10:00Z

- Fix Discogs Mozart → Beethoven pollution: family match requires composer gate
- Intake: strip leading prepositions / `performed by` tails; Discogs KB seed wins title
- Catalog: drop bare `piano` from Beethoven duo distinctive_tokens
- Gate: `test_mozart_piano_concerto_discogs_path_not_beethoven_cello_family` + runtime/identity/ambient 33 passed

## 2026-07-25T18:50:00Z

- Fixed Unknown composer: Chinese 《》 title parse + catalog soft aliases (CJK len≥2); added Dvořák Dumky catalog shelf
- Chinese locales: **简体 (zh-Hans)** + **繁体 (zh-Hant)** — script tags only
- Guide switcher: 简体 | 繁体 | English

## 2026-07-25T18:35:00Z

- External skill intake: **Agent Reach** (`Panniantong/Agent-Reach` @ `b4d52c46…`)
- Security audit → conditional allow as **search enabler only**
- Installed `skills/enabler-agent-reach/` (policy fence; social/cookie/CLI-install denied)
- Wired Jina deepen into `aulos-api` web_search / web-research + OPS toggle
- Verified: registry discovers enabler; web_research tests pass

## 2026-07-26T01:15:00Z

- Work Identity Catalog productized (REQ-006 / SPEC-008 / DOM-002 / ADR-004)
- Catalog schema + 5 works (Bach Goldberg/Cello, Beethoven duo, Chopin/Mahler slots)
- IdentityResolver wired into intake/scrub/ambient; RAG seeds catalog cards
- Removed work-name elif trees; identity authority is catalog YAML

## 2026-07-26T00:55:00Z

- Deep identity audit + fix: Bach cello suites pollution (Goldberg / Beethoven duo)
- Added `solo-cello-suites` family; hardened intake, scrub, ambient conflict gates
- SPEC-006 identity rules updated; hard-fail tests for cello suites + ambient

## 2026-07-25T17:15:00Z

- operating-defaults 0.4.0: product capabilities via Agent + Skill Harness; ADR-002 consequences updated

## 2026-07-25T17:00:00Z

- Timezone constraint promoted: store UTC / display OS local (operating-defaults 0.3.3)

## 2026-07-25T16:50:00Z

- Self-evolution closeout: process + facility + canonical source
- Memo: `docs/evolution-cycle-2026-07-25-harness-process-facility.md`
- Insights promoted; STATE/TASK_STACK updated for day organize + history-refresh
- Canonical library confirmed: `agilewayai/aries-harness-skills` (not studio)

## 2026-07-25T16:40:00Z

- Relocated harness **facility** assets into `.aries_harness/` across the fleet
- Was: project-root `scripts/aries-harness/` + `templates/aries_harness/`
- Now: `.aries_harness/scripts/` + `.aries_harness/templates/`
- Updated init/router usage strings, READMEs, operating-defaults 0.3.1, service-bootstrap
- Smoke: history-status / memory-inspect / well-organized OK from new paths

## 2026-07-25T16:25:00Z

- Fleet AGENTS.md / CLAUDE.md: Aries Harness promoted to **mandatory default (forced)**
- operating-defaults skill → 0.3.0; MEMORY snapshots across sub-projects updated
- Explicit: chat-only without harness artifacts is incomplete; waive only if operator says so

## 2026-07-25T16:20:00Z

- AUDIT-001: process compliance review — verdict **partial/late**, not developed under harness process
- Remediated F1/F2: refreshed STATE/TASK_STACK; registered REQ-005/SPEC-006/CKPT-005/VR-005/AUDIT-001 in REG+INDEX
- Honest claim: behavior shipped then self-evolution promoted; future slices must open RUN-* and SPEC/tests first

## 2026-07-25T16:15:00Z

- Promoted ambient/media/identity iteration into harness: REQ-005, SPEC-006, CKPT-005, insights
- Skill bumps: compose/eval 0.3.0, synthesize 0.2.0, corpus 0.3.0, listening router 0.2.0
- Gates: ambient hard-fail in eval; family list ownership + foreign-chamber scrub; media `inline`
- Tests: Beethoven ambient/parity, Goldberg pollution scrub, eval without ambient fails
- Operating default: every product iteration must promote into skill harness assets

## 2026-07-25T14:53:12Z

- Ambient theme audio + owner toolbar script in guide_render for /g share pages
- synthesize merges kb_dossier / rag_hits from API knowledge retrieve
- iter_listening_chain accepts kb_dossier, rag_hits, rag_mode


## 2026-07-25T14:35:00Z

- Bilingual Salon Codex: every guide now has EN + professional 中文 panes with language toggle (default 中文 when zh pack exists)
- Curated zh for Goldberg corpus + Beethoven cello family/composer cards; LLM prompt asks for nested zh JSON
- Guardrails strip skill/ops jargon from Chinese prose; Noto Serif SC for Chinese display

## 2026-07-25T14:20:00Z

- Cold-path Salon Codex parity: added `aulos-listening-synthesize` compounding composer cards + genre families (+ optional LLM JSON)
- Fixed ZH intake for Beethoven cello sonatas & variations; guide chambers now match Goldberg set offline (~17k vs ~20k HTML)
- API enrichment upgraded from 80-word note to structured Salon Codex JSON when ops LLM is live

## 2026-07-25T13:55:00Z

- designed Salon Codex ideal 导赏 (REQ/ARCH/SPEC-003): 12 chambers from thesis → portrait → genesis → stature → anatomy → sound → kindred → interpretations → YouTube/Discogs → practice → caveats
- flagship corpus `bwv-988-goldberg.yaml` with Haussmann portrait, Gould 1955/1981 Discogs masters, curated appreciation links
- SkillRuntime compose/eval 0.2.0; live API smoke html ~19k with all chamber markers

## 2026-07-25T11:36:00Z

- recorded fleet operating defaults: aries-harness for product design / architecture / spec / history-refresh / well-organized / devops
- coding loop default set to TDD (Red → Green → Refactor)
- UI/UX work must apply `ui-ux-pro-max`
- added skill `aulos-operating-defaults` and memory card `CARD-001-operating-defaults`
- propagated into workspace + all sub-project `AGENTS.md` / `CLAUDE.md` / `MEMORY.md`

## 2026-07-25T11:20:05Z

- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`
- no execution history recorded yet

## 2026-07-25T13:13:36Z

- Designed skill-powered 导赏 architecture (REQ-002 / ARCH-002 / ADR-002 / SPEC-002).
- Scaffolded domain-runtime family: aulos-listening(+intake/width/depth/corpus/compose/eval) with Goldberg corpus.
- Next: SkillRuntime in aulos-api/agent binding workflow steps to skill ids.

## 2026-07-25T13:23:08Z

- Longrun 1–4 done: SkillRuntime drives listening guides; skill_versions persisted; MCP skills.list/run; ops Skills tab; web shows skill ids.
- Verified: skills 5 / api 22 pytest; live Goldberg probe score=10; guide steps cite aulos-listening-*.

## 2026-07-25T13:34:45Z

- Closed residual 1–4: ops Disable now skips skill steps at runtime; SSE `/v1/listening-guides/stream`; web live chain; serve.py streams event-stream.
- Verified: skills 7 / api 24 pytest; SSE smoke on :5090 and proxy :5091.
