---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "managed-doc"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:d4a394100c09e953a6f5b5ca83c561ee1f37627d2c33ae99725f3fea1746bac6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Insights — aulos-skills durable baseline

## 2026-07-26 — Locale script tags only (promoted)

- Guide languages: **English / 简体 / 繁体** via `zh-Hans` and `zh-Hant`.
- Do not use regional locale abbreviations in open-source source, UI, or LLM prompts.
- Dossier keys: `zh` / `zh_hans` (simplified), `zh_hant` (traditional); synthesize Hant from Hans when missing.
- Measurable gate: `tests/test_intake_i18n.py` asserts `data-lang="zh-Hans|zh-Hant"` and switcher labels 简体|繁体.

## 2026-07-26 — Intake composer recovery (promoted)

- `Unknown composer` with clear Chinese 《书名》 text was intake failure, not missing LLM.
- Fix path: `intake_parse.guess_composer_and_title` + catalog shelf (e.g. Dumky) + compose recovery.
- Soft alias match: CJK aliases usable at length ≥ 2 (肖邦/巴赫).
- Gate: `tests/test_identity.py` Dumky resolve; `test_intake_i18n.py` no Unknown composer.

## 2026-07-26 — Agent Reach as fenced search enabler (promoted)

- Install truth: owner `Panniantong/Agent-Reach` pinned commit under `skills/enabler-agent-reach/`.
- Allow Jina deepen / optional Exa+gh read; deny cookies, social CLIs, `agent-reach` apt/npm install.
- OPS toggle: `agent_reach_enabled` on web-research config.

## 2026-07-26 — Professional Music Knowledge Plane (promoted)

- Encyclopedic music data (works, composers, history, discography) lives in
  **aulos-knowledge**, not in `aulos.db` with users/guides.
- Identity remains Catalog/Resolver (SPEC-008); content richness comes from the
  knowledge plane with allowlisted sources + artifact provenance (ADR-006).
- OPS **Knowledge** tab audits sources/jobs/documents/provenance.
- Enable RAG merge with `AULOS_KNOWLEDGE_PLANE_ENABLED=true`.

## 2026-07-26 — Work Identity Catalog is identity authority (promoted)

- **Root cause of cross-work pollution was missing identity entities**, not missing
  Bach-cello `if` branches. Procedural heuristics cannot productize Chopin/Mahler.
- **Catalog YAML is the authority** (`assets/catalog/`). Intake uses
  `IdentityResolver` only — no work-proper-name `elif` in runtime/ambient.
- **RAG enhances content after identity**; it must not alone decide the work.
- **Positive + negative identity:** `distinctive_tokens` + `conflict_work_ids` →
  derived `conflict_markers` for scrub/ambient.
- Adding a composer/work = authoring catalog records (+ optional family/dossier),
  not editing Python. Thin slots (Chopin nocturne, Mahler 5) prove extensibility.
- See REQ-006, SPEC-008, DOM-002, ADR-004.

## 2026-07-26 — Solo cello suites identity (superseded by Catalog)

- Earlier case patches (solo-cello family + scrub tuples) were symptom medicine.
- Behavior preserved via catalog record `bach.cello-suites.bwv-1007-1012`;
  implementation now Catalog-driven.

## 2026-07-25 — Agent-centric 导赏 (promoted)

- Product core is **Agent + Skill Harness + tools**, not API Python orchestration.
- Listening jobs: API injects RAG/context and persists; **aulos-agent** calls `run_listening_skill` per trigger.
- Do not reintroduce `SkillRuntime.iter_listening_chain` as the product entrypoint in `aulos-api`.

## 2026-07-25 — Timezone: store UTC / display OS local (promoted)

- API and DB store UTC; wire strings end in `Z` (`aulos_api.timefmt`).
- Product UIs (`aulos-web`, `aulos-ops`) format via `src/time.ts` using the OS/browser timezone.
- Do not show raw UTC ISO or force `timeZone: 'UTC'` in user-visible stamps.
- Harness Markdown history may remain UTC (shared operator docs).

## 2026-07-25 — Harness process + facility + source (promoted)

- **Aries Harness is forced, not preferred.** Charter files (`AGENTS.md` / `CLAUDE.md`)
  and `aulos-operating-defaults` must say mandatory; soft wording invites code-first skips
  (AUDIT-001).
- **Chat-only without harness artifacts is incomplete.** REQ/SPEC → TDD → Verify →
  JOURNAL/history-refresh; promote strategic lessons into insights/skills/gates.
- **Facility lives under `.aries_harness/`.** CLI helpers → `.aries_harness/scripts/`;
  init skeletons → `.aries_harness/templates/`. Never leave parallel copies at project-root
  `scripts/` or `templates/`.
- **Canonical library is `agilewayai/aries-harness-skills`.** Do not use obsolete
  `AriesHarnessStudio` / `aries-studio` clones as source of truth.
- **Close the day with organize + history.** `well-organized` then `history-refresh`
  so INDEX/STATUS/RETROSPECTIVE match the artifacts that shipped.

See: `docs/evolution-cycle-2026-07-25-harness-process-facility.md`

## 2026-07-25 — Ambient + identity (promoted)

- **Chamber coverage ≠ listening product.** Guides must ship a playable ambient surface
  and bilingual panes, not only Salon Codex headings.
- **Same-origin media first.** Origin CDNs fail silently; `/v1/media` cache→proxy→origin
  with `Content-Disposition: inline` is the playback contract.
- **Family scaffolds own cold-path structure.** LLM/RAG append-merge smuggles flagship
  (Goldberg) chambers into unrelated works — scrub + prefer family lists.
- **KB injection needs positive identity.** Empty `work_title` on a KB dossier must not
  pass the “different work” guard.
- **Eval must hard-fail missing ambient.** Soft notes alone did not prevent shipping
  silent players.
- **Studio sandbox is part of the harness.** `srcDoc` without `allow-scripts` /
  without `<base href>` makes ambient JS and relative media URLs appear “broken”.

## Earlier

- Cold-path Salon Codex parity via synthesize (REQ-004).
- Bilingual Salon Codex EN/ZH (SPEC-005).
- Flagship Goldberg corpus as chamber excellence reference (SPEC-003).
