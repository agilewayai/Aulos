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
content_fingerprint: "sha256:98bf720acea64989b219e1c67ee758eb5a38d5efb56989b6eb437a8eb7b0fd8d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Insights — aulos-skills durable baseline

Programmatic thinking promoted into **[META-001](../references/META-001-meta-principles.md)** carries `↑ META-001 §…`. Domain gates and YAML details stay here + in SPEC.

## 2026-08-02 — Multi-work guides need plural product structure

↑ META-001 §1 + §4.1 (data shape must match product shape)

- Guide #59 class continued: even after per-work composer/fold-back fixes, a
  three-work program remains fragile if final compose has only one article body.
- Class fix: emit `guide_sheets[]` as one sheet per work plus one synthesis sheet;
  expose `program_parallel_plan` so future gateway/agent workers can fan out
  work deepen and fan in to synthesis; render accessible sheet tabs in guide HTML.
- Boundary: skills own deterministic sheet contract and self-contained guide UI;
  actual parallel execution belongs to worker-safe gateway/agent orchestration.

## 2026-08-02 — Program loop must own final subject, not only chambers

↑ META-001 §1 + §4.1 (validate every stage; release structure before deepen)

- Guide #59 proved a program loop can be correct in the middle and still fail at
  the product boundary: structure was ready and 3/3 works deepened, but final
  album/family/LLM merge re-owned scalar subject fields and shipped
  `Unknown composer` + anonymous thin prose.
- Multi-work Discogs fix class: release structure must carry **per-work composer**
  into `g.program`; fold-back must rebuild final `composer`, thesis, introduction,
  related works, and sound world from program iterations; publish/persist gates must
  fail closed when eval/process says false.

## 2026-08-01 — Discogs release structure before deepen

↑ META-001 §4.1 (high covenant) · SPEC-034 / ARCH-002 / ADR-006

- Multi-work pressings must **fetch complete Discogs metadata → build program map →
  then deepen per work**. Family scaffolds before structure produce thin guides
  (Bach violin concertos album class).
- Artifact: `aulos.release_structure/v1`. Gate: `structure_ready`. Expand layers:
  metadata → program_map → work_deepen* → pressing_synthesis.
- Forbidden: case craft per release id; collapsing program into one family pack.

## 2026-08-01 — Compression: delete case patches, keep dimensional engine

↑ META-001 §1 (anti-case)

- Deleted pre-authored `craft/*.yaml` (were coverage-by-enumeration).
- Deleted localized review/scrub hardcodes; form_lock + facet dimensions remain.
- Catalog floor + family + dimension templates are the thicken path; craft only via promote.

## 2026-08-01 — Dimensional engine, not case patches (SPEC-031 / META-001 v6)

↑ META-001 §1 (class fix; anti-case for listening unknown titles)

- **Constraint:** Do not “fix” thin guides by authoring one craft/Catalog YAML per
  Discogs repro. Engine = FacetClassifier → dimension voices → stage → promote-production.
  YAML caches accelerate; they are not the mechanism.
- **Evidence:** two unrelated titles (lyric piano + string quartet) graduate on one
  pipeline in `tests/test_dimensional_promote.py`.

## 2026-08-01 — Promote staging closes the unknown-case loop (SPEC-030)

↑ META-001 §2 (asset sync with operator gate) + §1 (mechanism before Catalog write)

- **Symptoms:** promote_candidate was invisible and non-actionable; Discogs forms like
  prelude/etude fell through classifier.
- **Class fix:** staging craft write under `craft/staging/` + ops Stage surface;
  expanded facet tokens. Production craft/Catalog still require explicit future REQ.
- **Evidence:** promote staging unit + API tests; Guide quality Promote column.

## 2026-08-01 — Unknown-Case Thicken Loop (SPEC-029)

↑ META-001 §1 (mechanism over asset lists) + §3 (contracts as floor)

- **Symptoms:** Catalog/family/craft YAML only thicken known works; next Discogs/NLP
  cases fall to bare `generic-scaffold`.
- **Class fix:** FacetClassifier → archetype floor (reuse family pack or built-in
  `chamber-generic`) → chamber contracts → `promote_candidate` dry-run cache draft.
  YAML remains accelerator, not engine.
- **Evidence:** `tests/test_unknown_case_thicken.py` — Clara Schumann nocturne (non-Catalog)
  yields `archetype:lyric-piano-miniatures` + promote dry-run schema.

## 2026-08-01 — Catalog craft coverage + refuse-prose scrub protect (SPEC-028)

↑ META-001 §1 (class scrub bug) + §3 (craft assets as product floor)

- **Symptoms:** Only Mendelssohn had craft YAML; scrub wiped craft theses that named
  conflict works to refuse them (e.g. nocturne mentioning mazurka); thin Catalog
  composers (Dvořák) never got dossier builds unless manually triggered.
- **Class fix:** Craft pack for every Catalog work; protect `craft:` /
  `catalog-floor:` scalars from alien scrub; fleet
  `ensure_catalog_composer_dossiers` + ops endpoint.
- **Evidence:** 10/10 craft coverage tests; K.488 synthesize includes `craft:`;
  Dvořák dossier built (10 events / 142 works).

## 2026-08-01 — Genre family coverage closes Catalog gauze holes (SPEC-027)

↑ META-001 §1 (data/Catalog over heuristics) + §2 (asset sync)

- **Symptoms:** Concerto / requiem / symphony / trio Catalog works had `family_id: null`
  and no genre pack — catalog floor fell back to generic scaffold.
- **Class fix:** Four bilingual family packs + Catalog lock + synthesize hint prepend +
  craft-floor auto-load family by id; Mahler/Dvořák composer cards.
- **Evidence:** Every Catalog work has registered family; K.488 synthesize includes
  `family:piano-concerto+catalog-floor:…`.

## 2026-08-01 — Systemic cold thicken: catalog floor + asset_depth (SPEC-026)

↑ META-001 §1 (class fix over case packs) + §4 (knowledge plane async thicken)

- **Symptoms:** Thickness still required hand craft YAML / pre-built dossiers; arbitrary
  Catalog works stayed on family gauze; product score could still read “strong” on
  family-only shelves.
- **Class fix:** `build_catalog_craft_floor(work_id)` binds Catalog+family; thin dossier
  auto-enqueues build for *next* compose; ProductScorecard `asset_depth` caps honesty.
- **Evidence:** Chopin nocturne synthesize source includes `catalog-floor:…` without craft YAML.

## 2026-08-01 — Product vs process dual-track + digit alien bounds (guide #50)

↑ META-001 §1 (root-cause class) + §3 (hard-fail product gates) + §4 (knowledge plane separate)

- **Symptoms:** Process scorecard hard-failed on alien `988` because Discogs year
  `1988` substring-matched; `eval_pass` still mixed process honesty with reader craft;
  cold Mendelssohn shelf stayed thin without knowledge dossier / work craft pack;
  LLM poetic ZH overwrote craft theses after synthesize.
- **Class fix:** `marker_in_text` digit/word boundaries; ProductScorecard owns
  `eval_pass`; knowledge thicken + `assets/craft/{work_id}.yaml`; `reassert_craft_leads`
  at compose; persist `product_scorecard` in API research_json.
- **Evidence:** guide #50 process 76.1% hard_fail → 81.2% solid; product 100% strong;
  synthesize includes `craft:` + `knowledge-plane`.

## 2026-08-01 — Portrait / foreign-family dossier_id / H1 shadow (guide #48)

↑ META-001 §1 (multi-stage validate; class gates) + §3 (craft: no variable shadow)

- **Symptoms:** Bernstein as guide H1; Mozart alt text on Beethoven.jpg; Beethoven cello
  Op.69 / Goldberg stature reasons on Horowitz Mozart K.488.
- **Root causes:** (1) render loop reused `title` for video cards; (2) no portrait↔composer
  identity gate and no Mozart composer card; (3) KB-RAG shipped `dossier_id=family:duo-cello-piano`
  without `family:` in synthesize_source — decontam missed it; shared `piano` defeated
  instrument-miss; process scorecard/review not persisted on that ship path so self-heal never fired.
- **Rules:** identity hygiene on dossier_id + portrait every synthesize/compose; scorecard
  identity hard_fail feeds `critique_corrections`; never shadow H1 `title` in render loops.
- Gate: `tests/test_identity_hygiene.py`.

## 2026-07-27 — Authority Source Registry (promoted)

↑ META-001 §4 (knowledge plane + verified sources)

- Classical encyclopedic crawl/RAG may only use **registered + verified** sources
  (`aulos-knowledge` REQ-008 / ADR-006 / `data/registry/sources.yaml`).
- Job gate: enabled ∧ verified ∧ connector registered; fetch URLs ∈ base_urls;
  publish defaults to quarantine unless tier-S verified policy allows.
- Ops Knowledge Sources: register candidate → verify/reject/suspend.

## 2026-07-26 — Family evidence + per-node decontam (promoted)

↑ META-001 §1 (multi-stage validate; data/evidence over one-shot scrub)

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

↑ META-001 §3 (coerce external / LLM input)

- **Root cause:** `merge_dossiers` used `dict(layer["zh_hans"])` when DeepSeek returned
  Chinese prose (or a list) instead of an object →
  `ValueError: dictionary update sequence element #0 has length 1; 2 is required`.
- Hit Mozart piano-concerto jobs in `listening.synthesize` (hard fail) and web-research merge (soft warn).
- **Rule:** always `coerce_dict()` / `_as_dict()` before treating dossier chambers as mappings.
- Gate: `tests/test_salon_codex_merge.py`.

## 2026-07-26 — PG schema patch on every model change (promoted)

↑ META-001 §2 (schema parity; SQLite ≠ production)

- Production hot DB is Postgres; SQLite is failover mirror only.
- `Base.metadata.create_all` does not ADD columns on existing PG tables.
- Closeout rule: extend `aulos_api.db.schema_patches`, apply on primary+failover, verify PG columns after restart.
- Incident: SPEC-013 fields (`message`, `tags_json`, `favorited_at`, …) landed in SQLite ALTER path only → PG missing until dual-dialect patches.

## 2026-07-26 — Family pack composer gate (promoted)

↑ META-001 §1 (evidence gates; no form-only unlock)

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

→ operating-defaults (locales); not META

- Guide languages: **English / 简体 / 繁体** via `zh-Hans` and `zh-Hant`.
- Do not use regional locale abbreviations in open-source source, UI, or LLM prompts.
- Dossier keys: `zh` / `zh_hans` (simplified), `zh_hant` (traditional); synthesize Hant from Hans when missing.
- Measurable gate: `tests/test_intake_i18n.py` asserts `data-lang="zh-Hans|zh-Hant"` and switcher labels 简体|繁体.

## 2026-07-26 — Intake composer recovery (promoted)

→ SPEC-008 / identity tests (domain)

- `Unknown composer` with clear Chinese 《书名》 text was intake failure, not missing LLM.
- Fix path: `intake_parse.guess_composer_and_title` + catalog shelf (e.g. Dumky) + compose recovery.
- Soft alias match: CJK aliases usable at length ≥ 2 (肖邦/巴赫).
- Gate: `tests/test_identity.py` Dumky resolve; `test_intake_i18n.py` no Unknown composer.

## 2026-07-26 — Agent Reach as fenced search enabler (promoted)

→ enabler skill / OPS (domain)

- Install truth: owner `Panniantong/Agent-Reach` pinned commit under `skills/enabler-agent-reach/`.
- Allow Jina deepen / optional Exa+gh read; deny cookies, social CLIs, `agent-reach` apt/npm install.
- OPS toggle: `agent_reach_enabled` on web-research config.

## 2026-07-26 — Professional Music Knowledge Plane (promoted)

↑ META-001 §4 (knowledge plane boundary)

- Encyclopedic music data (works, composers, history, discography) lives in
  **aulos-knowledge**, not in `aulos.db` with users/guides.
- Identity remains Catalog/Resolver (SPEC-008); content richness comes from the
  knowledge plane with allowlisted sources + artifact provenance (ADR-006).
- OPS **Knowledge** tab audits sources/jobs/documents/provenance.
- Enable RAG merge with `AULOS_KNOWLEDGE_PLANE_ENABLED=true`.

## 2026-07-26 — Work Identity Catalog is identity authority (promoted)

↑ META-001 §1 + §4 (data over heuristics; identity before enrich)

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

↑ META-001 §1 (symptom medicine → Catalog)

- Earlier case patches (solo-cello family + scrub tuples) were symptom medicine.
- Behavior preserved via catalog record `bach.cello-suites.bwv-1007-1012`;
  implementation now Catalog-driven.

## 2026-07-25 — Agent-centric 导赏 (promoted)

↑ META-001 §4 (agent-centric product)

- Product core is **Agent + Skill Harness + tools**, not API Python orchestration.
- Listening jobs: API injects RAG/context and persists; **aulos-agent** calls `run_listening_skill` per trigger.
- Do not reintroduce `SkillRuntime.iter_listening_chain` as the product entrypoint in `aulos-api`.

## 2026-07-25 — Timezone: store UTC / display OS local (promoted)

→ operating-defaults (time); not META

- API and DB store UTC; wire strings end in `Z` (`aulos_api.timefmt`).
- Product UIs (`aulos-web`, `aulos-ops`) format via `src/time.ts` using the OS/browser timezone.
- Do not show raw UTC ISO or force `timeZone: 'UTC'` in user-visible stamps.
- Harness Markdown history may remain UTC (shared operator docs).

## 2026-07-25 — Harness process + facility + source (promoted)

↑ META-001 §2 (harness forced; facility; canonical library; Honeycomb)

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

↑ META-001 §3 (hard-fail gates) + §4 (listening product surface)

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
