---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "meta-principles"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T10:45:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:d001300e6f51b1384048ff81ec2bb4b36be22b6a67306213f85493c0a64f0809"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# META-001 — Meta Principles (纲领层原则)

Fleet-wide thinking and engineering principles for all `aulos-*` work. **Agents and humans must align with this document** before large slices, refactors, or cross-project changes.

Upstream: operator directive (2026-07-27); promoted from `docs/insights.md` + JOURNAL (v2).  
Downstream: `aulos-operating-defaults` skill, workspace `AGENTS.md`, per-project harness REG/SPEC.

## Status

| Field | Value |
| --- | --- |
| Artifact ID | META-001 |
| Version | v10 |
| Layer | MetaDefineLayer |
| Scope | Whole Aulos monorepo + harness fleet |
| Supersedes | v9 program loop without **final subject scalar ownership + failed-gate persistence** (§4.1) |

## How to use

1. **Session start** — skim §1–§4 when planning non-trivial work.
2. **Before coding** — if a principle conflicts with a shortcut, the principle wins unless the operator explicitly waives in the current turn.
3. **Closeout** — when a slice teaches a durable lesson, promote a one-line rule into `docs/insights.md` (with `↑ META-001 §x` when it is programmatic) or a SPEC/ADR; do not leave it chat-only (AUDIT-001).

---

## 1. Root-cause thinking (根本原因)

Solve problems at the source, not at the symptom.

| Do | Don't |
| --- | --- |
| Name the **failure mode** (what broke, for whom, under what input). | Patch UI copy or add retries without understanding why the failure happened. |
| Trace **data + control flow** across boundaries (web → API → skills → DB → external). | Fix one repo while leaving sibling assets inconsistent. |
| Prefer fixes that **remove the class of bug** (validation, contract, gate, data). | Stack special cases that only work for today's repro. |
| Record root cause in **JOURNAL** + tests/VR when non-obvious. | “Works on my machine” closeout without evidence. |

**Heuristics:**

- Ask “why” at least twice.
- If the same patch would land in three places → extract a shared contract, helper, or **data record**.
- If the third similar case patch appears → stop writing Python `if` branches; author Catalog / SPEC / YAML instead (**data over heuristics**).
- Multi-stage pipelines must **validate at each stage** that can reintroduce pollution (scrub once at the end is not enough).
- **Listening unknown-case (SPEC-029–031):** thickness must come from **facet dimensions +
  promote pipeline**, not from enumerating famous works one-by-one. Catalog/craft/family
  YAML are **accelerators/caches**, never the engine. Forbidden as the “fix”:
  `if mendelssohn`, guide-#N special cases, or shipping one craft YAML solely to silence
  a single Discogs repro. Tests must prove **≥2 unrelated identities** on the same path.

**Promoted examples:**

| Incident | Symptom medicine | Root cause / class fix |
| --- | --- | --- |
| Cross-work chamber pollution | composer/`if bach` scrub lists | Missing **identity entities** → Catalog + IdentityResolver (SPEC-008) |
| Same-composer sibling swap (Horowitz Mozart K.488 → Requiem/末日经) | hope LLM stays on title; per-work if lists | **Identity lock class gate**: catalog numbers + `form_lock_groups.yaml` aliens + dossier betrayal reject + compose HTML re-scrub (`identity_lock.py`) — Catalog work YAML improves recall but is not required for the form/number lock |
| Family unlock on form alone | one-shot synthesize scrub | Evidence gates + **per-node decontam** (SPEC-009) |
| Dev Blog missing AUDIT-009 | “LLM forgot” | Evidence collector truncated **newest** journal entries |
| Solo cello suites | case-specific scrub tuples | Catalog record (symptom path superseded) |
| Thin Discogs/NLP guides (unknown titles) | hand craft YAML / per-work thicken | **FacetClassifier → dimension templates → stage → promote-production** (SPEC-029–031) |
| Multi-work Discogs album → thin family scaffold | hope one IntentLock title thickens | **Release structure first** (§4.1 / SPEC-034): full fetch → program map → layered deepen |
| Program loop ran but chambers = Bach bio / Bachlava junk | keep Discogs `A = B = C` titles; hard-fail when LLM 401 | **Canonical program title + catalog-first search**; **LLM is enrich not gate** — web_search_raw floor on verify fail (§4.1) |
| Program loop ran but final guide = `Unknown composer` / anonymous thin prose | trust map/deepdives while album/family/LLM scalars keep control; persist `eval_pass=false` as completed | **Fold-back owns final subject scalars** — per-work composer into `g.program`, program-loop composer/thesis/introduction/related/sound overrides generic layers; failed eval/process gates persist as `failed` (§4.1) |

Domain detail stays in `docs/insights.md` and SPEC-008/009; this section owns the **thinking pattern**.

---

## 2. Asset synchronization & coordination (资产协同)

The monorepo is one product surface. **Artifacts must stay aligned.**

### 2.1 Asset classes

| Class | Examples | Sync rule |
| --- | --- | --- |
| **Behavior contract** | REQ, SPEC, SKILL.md | Change behavior → update contract **before** broad code. |
| **Harness run state** | STATE, TASK_STACK, JOURNAL, EVAL, VR | Close slice → update same turn as code. |
| **Cross-project promotion** | listening-product, auth, deploy | Canonical spec in owning project; consumers link, don't fork. |
| **Generated / derived** | `history/*`, Dev Blog posts, `dist/`, `version.json` | Regenerate after source truth changes (Honeycomb, build, dev-blog generate). |
| **Harness facility** | `.aries_harness/scripts/`, `templates/` | Never leave parallel copies at project-root `scripts/` or `templates/`. |
| **Runtime config** | `.run/host.env`, systemd units | Never commit secrets; document keys in `deploy/OPS.md`. |

### 2.2 Coordination rules

1. **Harness is forced** — soft “prefer harness” wording invites code-first skips (AUDIT-001). Chat-only without REQ/SPEC/JOURNAL/tests is **incomplete**.
2. **Single source of truth** — one canonical SPEC/SKILL per behavior; other projects reference by ID/path. Canonical harness library: `agilewayai/aries-harness-skills` (not obsolete studio clones).
3. **Same slice, same story** — if API and Ops UI change together, one JOURNAL narrative or explicit cross-refs in both projects.
4. **Schema parity** — DB model change → `schema_patches` + PG verify (SQLite pilot ≠ production).
5. **Deploy is part of delivery** — local green ≠ production; close with deploy/smoke when the slice is meant to be live (Discogs OPS UI incident).
6. **Version drift** — portal builds emit `version.json`; clients poll and hard-reload; don't rely on sticky `index.html` cache.
7. **Honeycomb closeout** — `well-organized` + `history-refresh` so fleet `history/` matches JOURNAL/STATE.

### 2.3 Red flags (desync)

- Code merged but no SPEC/JOURNAL/TEST update.
- Harness daily summary contradicts Dev Blog or git log (or derived evidence truncates newest facts).
- Duplicate conflicting rules in chat vs `AGENTS.md` vs SKILL.
- Large commit message hiding multiple independent behavior changes.
- Facility scripts duplicated outside `.aries_harness/`.

---

## 3. Engineering craft & code health (工程实践)

Prefer small, clear, test-backed changes over clever or sprawling diffs.

### 3.1 Practices

| Principle | Practice |
| --- | --- |
| **TDD** | Red → Green → Refactor; gate in `EVAL` / pytest when behavior is user-visible or regression-prone. |
| **Minimal scope** | Smallest correct diff; no drive-by refactors in unrelated files. |
| **Conventions** | Match surrounding module naming, types, and error style. |
| **Seams over monoliths** | Split when a file owns multiple reasons to change (SPEC-016 / AUDIT-009 F10). |
| **DRY before second copy** | The **second** identical (or near-identical) UI block / helper / pipeline step must be an extract, not a paste. See §3.5. |
| **Explicit contracts** | Types, Pydantic models, SPEC acceptance — not implicit dict shapes from LLM/HTTP. |
| **Coerce external input** | Always `coerce_dict()` / schema-validate before treating LLM or web payloads as mappings. |
| **Hard-fail product gates** | Soft notes alone do not prevent shipping broken UX (e.g. missing ambient player). |
| **Safe defaults** | Fail closed for auth, HTML, secrets; no silent swallow of errors that hide product bugs. |

### 3.2 Code smells to avoid

- **Duplicated code (copy-paste)** — same markup, progress math, or join/coerce logic forked across surfaces (e.g. Studio Atelier vs 我的聆乐导赏工坊). **Forbidden as a delivery shape**; extract a shared module/component first (§3.5).
- **Shotgun surgery** — one concept changed in many unrelated files without a shared abstraction.
- **Divergent duplicate** — same logic copied in web and ops (or diary and studio) then edited differently until they disagree.
- **Boolean blindness** — `busy` flags that block entire app when only one panel is working.
- **Chat-only fixes** — behavior change with no test or harness artifact.
- **Evidence truncation** — summarizers that drop newest facts (journal tail-bias, LLM hype in Dev Blog).
- **Hardcoded domain** — composer/work literals in Python instead of Catalog + IdentityResolver.
- **Symptom medicine** — third case-specific scrub/`if` instead of Catalog or contract.
- **Sync long work on HTTP** — slow jobs must enqueue (mail, listening, ops tasks); UI stays interactive.

### 3.3 Long-running work & task queues

Work that may take seconds or longer **must not block** HTTP request threads or freeze operator UIs.

| Rule | Practice |
| --- | --- |
| **Enqueue** | Return **202 Accepted** (or equivalent) with a durable task/run id — not a hung connection. |
| **State machine** | Model explicit lifecycle: `queued` → `running` → `completed` \| `failed` (or domain-specific terminal states). |
| **Durable row** | Persist status, timestamps, payload/result, and `error` on the owning service DB for audit and replay. |
| **Worker** | Background thread, Redis queue, or dedicated worker process executes the job; HTTP only enqueues. |
| **UI** | Poll task/run status or subscribe to events; show in-flight state; link to unified Ops **Tasks** when applicable. |
| **Sync escape hatch** | `*_SYNC` / test flags may run inline in CI only — never rely on sync mode in production UX. |

**Examples:** dev blog generate (`dev_blog.generate`), knowledge benchmark (`knowledge.benchmark`), listening guide compose, mail send, crawl/fetch jobs.

### 3.4 Product interaction — Meta Play Simple (产品交互)

Operators and listeners interact with a **product**, not with internal plumbing. Every surface must be designable as a simple playable story.

| Rule | Practice |
| --- | --- |
| **Human nouns first** | Entry points are people, works, places, stories — not IDs, QIDs, connector names, or YAML paths. |
| **Progressive disclosure** | Hide technical fields (QID, depth, rate limits) behind Advanced; defaults must be enough to start. |
| **Seed the world** | Ship curated seed networks (famous composers, portraits, A–Z browse) so the first click is meaningful. |
| **One job, one viewport** | Each screen answers one user question; do not dump admin tables as the primary UX. |
| **Visible state** | Selection, loading, empty, and success are first-class; never a blank form waiting for expert knowledge. |
| **Same bar as consumer UX** | Ops/admin consoles follow the same clarity bar as the listening product — “internal tool” is not an excuse. |

**Anti-patterns:** requiring Wikidata QIDs to explore; empty search with no suggestions; raw API params as the only control; shipping a feature that only the implementer can operate.

When building knowledge / crawl / explore flows, start from **who** (composer) and **what** (work), then derive IDs server-side.

When smell is found during audit, open SPEC/ADR or insight — don't only fix the instance.

### 3.5 DRY — no duplicated product code (禁止重复实现)

**Rule:** If two product surfaces need the same interaction or calculation, they share **one** implementation. Copy-paste to ship faster is a **defect**, not a shortcut.

| Do | Don't |
| --- | --- |
| Extract shared component/helper **before** or **as part of** the second consumer (e.g. `AtelierTrail` for Studio + 我的聆乐). | Paste progress-bar / step-list markup into a second page and tweak labels only. |
| Put shared pure logic in a tiny util module with a unit test. | Re-derive `done/total/%` with the same filter set in three JSX blocks. |
| Prefer one SSE/watch helper used by multiple screens. | Fork event-consumption loops that drift apart. |
| Allow **params** (labels, empty copy, className) — not a second component tree. | “Almost the same” private forks that silently diverge. |

**Gate before merge/deploy:**

1. Search for near-duplicate JSX/CSS/helpers introduced in the slice.
2. If the same structure appears twice → extract; do not ship the fork.
3. Record the shared seam in JOURNAL (path + consumers).

**Promoted example (2026-08-01):** Diary guide atelier initially forked Studio chain UI → collapsed into `aulos-web/src/AtelierTrail.tsx` + `atelierTrailUtils.ts`. Plaza vs 我的聆乐 cards → `ListeningPostCard` + `sourceKind.ts`. Legacy skills `render_guide_html` fork → deleted; shared `html_bits` for point coerce + list HTML. Discogs analyze/snapshot → `_parse_release_core`; Studio/diary Discogs UI → `DiscogsReleasePicker` + `useDiscogsSearch`.

---

## 4. Architecture boundaries (架构边界)

Stable seams for the listening product and ops stack. Detail lives in SPEC/ADR; this section forbids re-blurring the lines.

| Boundary | Rule |
| --- | --- |
| **Agent-centric product** | Core is **Agent + Skill Harness + tools**. API injects context/RAG and persists; do not grow `aulos-api` into the listening orchestration entrypoint. |
| **Identity before enrich** | Catalog + IdentityResolver decide the work; RAG / knowledge / LLM **enrich after** identity — they must not alone choose `work_id`. |
| **Release structure before deepen** | See **§4.1** — Discogs multi-work pressings are programs; full metadata → structure map → layered expand. Forbidden: family-scaffold thicken before program recognition. |
| **Adversarial process review** | After each atelier node: deterministic IntentLock review; after synthesize/compose: review-only LLM Critic against the frozen lock (REQ-008 / SPEC-018 / ADR-005). Critic never rewrites identity. |
| **Knowledge plane** | Encyclopedic music data lives in **aulos-knowledge**, not mixed into `aulos.db` with users/guides. **Authority sources** must be registered and **verified** in the Source Registry (`data/registry/sources.yaml` / REQ-008) before crawl or RAG publish. |
| **Listening product surface** | A guide is chambers + bilingual panes + **playable ambient**, not headings alone (SPEC-005/006). Media contract and sandbox are part of the product. |
| **Security / HTML** | Guide HTML and session cookies follow SPEC-014/015; fail closed; module seams per SPEC-016. |

### 4.1 Release structure before deepen (唱片结构先于深化) — high covenant

**Operator-grade rule for every Discogs-sourced listening path.** Classical pressings
are often **multi-work programs**. Treating the album title as one work and jumping
into a genre family scaffold is a **class defect**.

| Stage | Obligation |
| --- | --- |
| **1. Fetch complete** | Pull the full Discogs release/master payload: credits (`artists` / `extraartists`), `tracklist` (incl. headings), `formats`, `labels`/`catno`, `images`, `genres`/`styles`, `master_id`. Title-only seeds are insufficient. |
| **2. Structure (canonical titles)** | Build `ReleaseStructure` (`aulos.release_structure/v1`). Collapse Discogs polyglot track titles (`EN = DE = FR`) via `canonical_discogs_title` — **never** prefer the longest string. Program labels must be catalog-bearing and search-safe. |
| **3. Gate** | `structure_ready` must hold before corpus/synthesize/thicken deepen. Incomplete program maps hard-fail — do not ship thin family prose. |
| **4. Iterative expand (LLM-optional)** | Loop **per program work** with **catalog-first `program_search_query`**: web gather → **usable floor even if LLM verify/enrich fails** (`web_search_raw`) → optional LLM thicken → fold (`release-program-loop`). Album-title web must not short-circuit. Filter composer-bio / junk hits that lack catalog or work tokens. |
| **5. Pressing synthesis** | Recording-level interpretations / vinyl / comparative shelf across the program. |

**Hard rules**

- **LLM is enrich, not a gate.** Auth failure / parse failure / not-ready must degrade to a snippet floor and continue the loop — never empty the iteration because verify returned `{}`.
- **Search query ≠ Discogs track title.** Use composer + catalog display (`BWV 1041`) + short canonical cue. Polyglot `=` titles are a class defect at structure time.
- **A correct middle stage is not a correct guide.** The program loop owns final
  subject scalars (`composer`, thesis, introduction, related works, sound world)
  after merge; failed eval/process gates must not be persisted or published as
  completed guides.

**Do / Don't**

| Do | Don't |
| --- | --- |
| Keep the album program visible in research / snapshot / atelier. | Collapse BWV/K./Op. siblings into one longest track before mapping. |
| Canonicalize program titles before web/LLM. | Feed `A = B = C` Discogs strings into search or map labels. |
| Deepen each program work with its own identity lock + catalogs. | Run `family:violin-concerto` (or any family) as a substitute for missing program structure. |
| Keep web snippets when LLM 401/unavailable. | Treat `verify_failed` / LLM auth as “skip community / stop deepen”. |
| Preserve Discogs performers/label as pressing-level layer 5. | Case-patch one Philips/DG release id with craft YAML. |

Canonical detail: **REQ-024 / SPEC-034 / ARCH-002 / ADR-006 / DOM-003**.
Related: SPEC-033 (instrument-faithful + multi-catalog title), SPEC-032 (identity freeze).

---

## 5. Relationship to other纲领 artifacts

| Artifact | Role |
| --- | --- |
| `aulos-operating-defaults` SKILL | Operational loop (Harness, Honeycomb, time, locales, deploy). |
| **META-001** (this doc) | **Why and how to think** — root cause, asset sync, craft, architecture boundaries. |
| REG-001 | Index of all managed artifacts; must list META-001. |
| SPEC-* | Behavior contracts per feature. |
| ADR-* | Durable technical decisions with trade-offs. |
| `docs/insights.md` | Incident-backed lessons; domain detail; link `↑ META-001 §x` when promoted to纲领. |

**Precedence:** META-001 + operating-defaults + workspace `AGENTS.md` → project MISSION/STATE → active SPEC for the slice.

### Domain index (not duplicated here)

| Topic | Canonical detail |
| --- | --- |
| Work identity / Catalog | SPEC-008, DOM-002, ADR-004, insights “Work Identity Catalog” |
| Discogs release structure before deepen | SPEC-034, ARCH-002, ADR-006, DOM-003, REQ-024, §4.1 |
| Family / decontam | SPEC-009, insights “Family evidence…” |
| Locales Hans/Hant | operating-defaults + insights “Locale script tags” |
| UTC / local display | operating-defaults + insights “Timezone” |
| Ambient / media | SPEC-005/006, insights “Ambient + identity” |
| Knowledge source registry | aulos-knowledge REQ-008, ADR-006, REG-SRC-001 |
| AUDIT-009 findings | `runs/reviews/AUDIT-009-…`, SPEC-014/015/016, ADR-008 |

---

## 6. Acceptance

- META-001 registered in `REG-001` (aulos-skills + workspace pointer).
- `aulos-operating-defaults` and workspace `AGENTS.md` / `CLAUDE.md` reference META-001.
- Agents treating Meta Principles as mandatory unless operator waives for the current turn.
- Insights that encode programmatic thinking carry `↑ META-001 §…` back-links.
