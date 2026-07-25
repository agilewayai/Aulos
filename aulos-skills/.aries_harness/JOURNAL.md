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
content_fingerprint: "sha256:0671c7f4c9e45f1d94c53d2a662ec7ee7c59a63a0c51a2ca6be0c5c0ec2c8313"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

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
