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
content_fingerprint: "sha256:60b1f5e8aecbf219046cf4b1675750ffe5e789903c9629c28fa644a298b81489"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

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
