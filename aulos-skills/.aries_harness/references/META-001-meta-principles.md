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
effective_since: "2026-07-27T10:50:00Z"
content_fingerprint: "sha256:37217f2ced82b0d5c2401a835793a8a2123392e8c6c2e028e320472b132f6179"
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
| Version | v4 |
| Layer | MetaDefineLayer |
| Scope | Whole Aulos monorepo + harness fleet |
| Supersedes | ad-hoc “common sense” in chat only |

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

**Promoted examples:**

| Incident | Symptom medicine | Root cause / class fix |
| --- | --- | --- |
| Cross-work chamber pollution | composer/`if bach` scrub lists | Missing **identity entities** → Catalog + IdentityResolver (SPEC-008) |
| Family unlock on form alone | one-shot synthesize scrub | Evidence gates + **per-node decontam** (SPEC-009) |
| Dev Blog missing AUDIT-009 | “LLM forgot” | Evidence collector truncated **newest** journal entries |
| Solo cello suites | case-specific scrub tuples | Catalog record (symptom path superseded) |

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
| **Explicit contracts** | Types, Pydantic models, SPEC acceptance — not implicit dict shapes from LLM/HTTP. |
| **Coerce external input** | Always `coerce_dict()` / schema-validate before treating LLM or web payloads as mappings. |
| **Hard-fail product gates** | Soft notes alone do not prevent shipping broken UX (e.g. missing ambient player). |
| **Safe defaults** | Fail closed for auth, HTML, secrets; no silent swallow of errors that hide product bugs. |

### 3.2 Code smells to avoid

- **Shotgun surgery** — one concept changed in many unrelated files without a shared abstraction.
- **Divergent duplicate** — same logic copied in web and ops instead of one module or API.
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

---

## 4. Architecture boundaries (架构边界)

Stable seams for the listening product and ops stack. Detail lives in SPEC/ADR; this section forbids re-blurring the lines.

| Boundary | Rule |
| --- | --- |
| **Agent-centric product** | Core is **Agent + Skill Harness + tools**. API injects context/RAG and persists; do not grow `aulos-api` into the listening orchestration entrypoint. |
| **Identity before enrich** | Catalog + IdentityResolver decide the work; RAG / knowledge / LLM **enrich after** identity — they must not alone choose `work_id`. |
| **Knowledge plane** | Encyclopedic music data lives in **aulos-knowledge**, not mixed into `aulos.db` with users/guides. **Authority sources** must be registered and **verified** in the Source Registry (`data/registry/sources.yaml` / REQ-008) before crawl or RAG publish. |
| **Listening product surface** | A guide is chambers + bilingual panes + **playable ambient**, not headings alone (SPEC-005/006). Media contract and sandbox are part of the product. |
| **Security / HTML** | Guide HTML and session cookies follow SPEC-014/015; fail closed; module seams per SPEC-016. |

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
