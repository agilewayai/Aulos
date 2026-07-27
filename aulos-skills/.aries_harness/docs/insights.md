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
content_fingerprint: "sha256:f60e49b1e672ded519ea273d000a9ecc3334b756359f7696aa817a358e2122fe"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Insights — aulos-skills durable baseline

## 2026-07-26 — Family evidence + per-node decontam (promoted)

- **Root cause (guide #44):** composer-scoped family packs scored `+2` on surname alone
  (`brahms` → `duo-cello-piano`) with **zero** instrument/form evidence. Scrub only ran
  once at synthesize; unknown Discogs works had empty `conflict_markers`, so Beethoven
  cello chambers and Bach Suite peer ambient shipped as the Brahms violin shelf.
- **Rules:** (1) `match.composers` families require evidence ≥1 from instruments∪forms;
  (2) after synthesize/width/depth/compose, decontam validate → scrub + one rework
  (`refuse_families` / expanded markers); (3) ambient related packs must not unlock on
  bare form when composers[] is set to another name; era-peer packs with peers[] require
  peer hit; (4) do not put intentional peer tokens (`无伴奏`) on conflict_markers when
  related_works/ambient legally use them.
- Gate: `test_brahms_violin_concerto_not_duo_cello_family` (SPEC-009).

## 2026-07-26 — Never bare-dict LLM zh layers (promoted)

- **Root cause:** `merge_dossiers` used `dict(layer["zh_hans"])` when DeepSeek returned
  Chinese prose (or a list) instead of an object →
  `ValueError: dictionary update sequence element #0 has length 1; 2 is required`.
- Hit Mozart piano-concerto jobs in `listening.synthesize` (hard fail) and web-research merge (soft warn).
- **Rule:** always `coerce_dict()` / `_as_dict()` before treating dossier chambers as mappings.
- Gate: `tests/test_salon_codex_merge.py`.

## 2026-07-26 — PG schema patch on every model change (promoted)

- Production hot DB is Postgres; SQLite is failover mirror only.
- `Base.metadata.create_all` does not ADD columns on existing PG tables.
- Closeout rule: extend `aulos_api.db.schema_patches`, apply on primary+failover, verify PG columns after restart.
- Incident: SPEC-013 fields (`message`, `tags_json`, `favorited_at`, …) landed in SQLite ALTER path only → PG missing until dual-dialect patches.

## 2026-07-26 — Family pack composer gate (promoted)

- **Root cause:** `_match_family` unlocked `duo-cello-piano` on bare `piano`+`sonata`
  (score≥2) with **no composer hit** → Beethoven cello chambers polluted Discogs Mozart
  piano concerto/sonata guides (K.488 / K.333).
- **Rule:** when a family YAML lists `match.composers`, require a composer token match
  (blob or `composer_guess`) unless `family_hints` explicitly forces the family.
- Discogs `/` cold path: intake prefers `kb_dossier` provenance seed; do not invent
  Catalog work_id/family from form overlap alone.
- Intake: strip leading prepositions (`to`/`by`/…) and `performed by…` tails from
  composer/title guesses — no per-composer branches.
- Gate: `test_mozart_piano_concerto_discogs_path_not_beethoven_cello_family`.

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
