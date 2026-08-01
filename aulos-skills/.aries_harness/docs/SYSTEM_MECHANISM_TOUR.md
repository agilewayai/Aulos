---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "managed-doc"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T21:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T21:30:00Z"
content_fingerprint: "sha256:8301050e864abc9329c4353996ee0bc8735c85f10e81eb676afa9dd6586b79b6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# System Mechanism Tour — Listening Atelier (规律层全盘导览)

**Lens:** system / mechanism / higher-dimensional law.  
**Not this doc:** per-work YAML stories, guide-#N patches, composer `if` trees.

Upstream: META-001 v6 · ADR-004 · ARCH-002/004 · SPEC-008…031.

---

## 0. One sentence

Aulos listening is a **gated atelier**: resolve identity → thicken a Salon Codex dossier by **dimensional floors + optional caches** → compose bilingual HTML → adversarial review/revise → dual scorecards → optionally **graduate** survivors into Catalog/craft via operator promote.

**Engine ≠ cache.** Facets + contracts + promote pipeline are the engine. Catalog / family / craft YAML accelerate known shelves.

---

## 1. Fleet topology

```text
Listener (aulos-web)
        │
        ▼
   aulos-api  (gateway preflight — identity/RAG/LLM seed; NOT skill orchestration)
        │  AgentProxy → aulos-agent tools
        ▼
   SkillRuntime atelier chain (aulos-skills)
        │
        ├── aulos-knowledge  (composer dossier / knowledge-plane thicken)
        └── aulos-ops        (Guide quality, promote stage/production)
```

**Boundary law:** API seeds context (`g.discogs` → `g.identity` → `g.rag` → `g.web`/`g.extweb` → `g.llm` → `g.agent` → `g.persist`). Agent owns skill order; skills own domain. API must not call `SkillRuntime.iter_listening_chain` as product orchestration.

| Plane | Role |
| --- | --- |
| Product UI | Request + read guide |
| API gateway | Persist guide, seed context, call agent, proxy knowledge |
| Skills runtime | Deterministic atelier chain + gates |
| Knowledge plane | Composer dossier / timeline / portrait (thicken, not identity) |
| Ops | Scorecards, traces, promote staging → production |

---

## 2. Atelier chain (control flow)

Canonical triggers (`SkillRuntime._run_route`):

```text
intake → corpus → synthesize → width → depth → compose
      → external_review → revise → eval
```

| Stage | Mechanism job |
| --- | --- |
| **intake** | Parse message/Discogs chrome → Work Resolver / Catalog IdentityResolver → IntentLock seeds |
| **corpus** | Optional curated flagship dossier (offline excellence) |
| **synthesize** | Layer-merge Salon Codex; provenance in `synthesize_source` |
| **width / depth** | Expand breadth / landmarks from dossier |
| **compose** | Render bilingual HTML + ambient; scrub foreign chambers |
| **external_review** | Expert hard-flaw pass (form-lock aliens, hygiene, prose) |
| **revise** | Deterministic repair + targeted chamber revise |
| **eval** | Process + product scorecards; pass/fail gates |

**Per-node rework (class law):** decontam and Intent Critic may re-run a node once (`SPEC-009` / `SPEC-018`). Scrub-only-at-end is forbidden.

---

## 3. Identity law (before RAG)

ADR-004 / SPEC-008:

1. **Catalog YAML is identity authority** when it hits.
2. **IdentityResolver** is generic scoring — no work-name Python branches.
3. **RAG must not alone decide work identity**; attach only when `work_id` / `corpus_key` matches.
4. **IntentLock + form_lock_groups** oppose sibling-form swaps (concerto ↔ requiem, etc.) even on Catalog miss.

Supporting modules:

| Module | Law |
| --- | --- |
| `identity.py` | Load Catalog; resolve |
| `work_resolver.py` | Discogs/title → Catalog work when possible |
| `identity_lock.py` | Catalog numbers + form-family aliens |
| `identity_hygiene.py` | Portrait / foreign-family dossier gates |
| `intake_parse.py` / `prose_hygiene.py` | Packaging title → listening title (form-cycle canons, not per-work) |

---

## 4. Thicken stack (the core mechanism)

### 4.1 Two paths, one law

```text
ANY title
   │
   ├─ Catalog hit ──► family hint → catalog-floor → (optional craft if promoted)
   │                  → knowledge-plane → chamber contracts
   │
   └─ Catalog miss ─► FacetClassifier → archetype/family pack OR dimension template
                      → promote_candidate (dry-run) → operator stage → production
```

### 4.2 Engine vs accelerator

| Layer | Kind | Role |
| --- | --- | --- |
| **FacetClassifier** | Engine | title/message → instruments × forms × era + archetype_id |
| **Dimension templates** | Engine | bilingual floor from facet voices (`dimension:{inst}+{form}`) |
| **Chamber contracts** | Engine | thesis/map/width/depth floors + ZH parity |
| **Form lock / decontam / hygiene** | Engine | refuse foreign chambers at each stage |
| **Promote pipeline** | Engine | dry-run → staging → Catalog stub + craft (operator) |
| Family YAML packs | Accelerator | Genre floor when registered |
| Catalog works/composers | Accelerator | Identity + catalog-floor bind |
| Craft YAML | Accelerator | **Only** after promote-production (no hand-seeded craft required) |
| Composer cards / corpus | Accelerator | Portrait / flagship excellence |
| Knowledge dossier | Accelerator | Portrait/timeline genesis thicken |

### 4.3 Provenance string

`synthesize_source` is the audit trail, e.g.:

- Known: `family:…+catalog-floor:{work_id}+knowledge-plane`
- Unknown: `archetype:…+dimension:{inst}+{form}`
- After promote craft exists: may include `craft:{work_id}`

### 4.4 Promote graduation (SPEC-029→031)

```text
synthesize emits promote_candidate (dry_run)
        │
        ▼
ops Stage → craft/staging/{id}.yaml  (status=staged)
        │
        ▼
ops Promote to production → Catalog composer/work stubs + craft/{id}.yaml
        │
        ▼
caches cleared; next resolve can treat as Catalog shelf
```

Invariant: **same code path for ≥2 unrelated identities**; no work-named branches.

---

## 5. Quality gates (dual track)

| Gate | Artifact | Asks |
| --- | --- | --- |
| **ProcessScorecard** | per-node + rollup | Pipeline honesty, identity, decontam, ambient… |
| **ProductScorecard** | HTML + dossier | Thesis/map, bilingual, atelier coverage, **asset_depth** |
| **Chamber contracts** | dossier | Craft floors before publish |
| **Eval** | combined | `eval_pass` follows product band + process hard fails |

**asset_depth law (systemic):** family/dimension alone cannot claim `strong` on identity-resolved shelves; catalog-floor / craft / knowledge deepen the band.

---

## 6. Pollution & repair laws

| Mechanism | Where | Law |
| --- | --- | --- |
| Family evidence gate | synthesize match | Composer-scoped packs need instrument/form evidence |
| Foreign family refuse | hygiene + decontam | `family:*` instruments miss title → drop |
| Form-lock aliens | identity_lock + external_review | Data policy YAML, not marker tuples in Python |
| Packaging hygiene | prose_hygiene | Discogs multi-lang dumps → form-cycle / primary segment |
| Process-lock ban | compose/revise/product score | No `CRITIQUE LOCK` in product HTML |
| Ambient | ambient_agent | No library rotation of wrong works; embed\|stream fallback |

---

## 7. Data & persistence

| Store | Contents |
| --- | --- |
| `listening_guides` | HTML, steps, `research_json` (dossier, scorecards, promote, chain_trace, synthesize_source) |
| Catalog assets | composers/works/index + form_lock_groups + weak_tokens |
| Family / composer cards | synthesize assets |
| `craft/` + `craft/staging/` | promote outputs only |
| Knowledge DB | composer dossiers (separate plane) |

---

## 8. Operator loop (ops)

Guide quality panel:

1. Scorecard board (process band, asset_depth, promote status)
2. Trace: process nodes + product dims + promote draft
3. **Stage craft** → **Promote to production** (system pipeline copy)

No per-work ops scripts required for unknown titles.

---

## 9. SPEC map (mechanism chronology)

| SPEC | Mechanism contribution |
| --- | --- |
| 008 | Catalog IdentityResolver |
| 009 | Per-node decontam + family evidence |
| 018/019 | Adversarial critic + process scorecard |
| 022 | External review → revise round |
| 023 | Product-prose hygiene |
| 024 | Work resolver + chamber contracts |
| 025 | Knowledge thicken + ProductScorecard |
| 026 | Catalog craft floor + asset_depth |
| 027 | Family coverage as Catalog accelerator |
| 028 | Craft-as-coverage (**superseded** as required; craft now promote-only) |
| 029 | Unknown-case FacetClassifier + archetype |
| 030 | Promote staging + ops surface |
| 031 | Dimension templates + promote-to-production |

---

## 10. Invariants checklist (regression forbidden)

1. No `if <composer|work_id|guide_id>` thicken branches in runtime.
2. Unknown titles still emit bilingual floor via facets/dimensions.
3. Catalog miss does not require hand craft YAML to be non-empty.
4. Promote path is case-agnostic (tests use ≥2 unrelated titles).
5. Foreign chambers caught by form_lock / hygiene / decontam — not celebrity/op-number Python lists.
6. Harness: REQ/SPEC → TDD → JOURNAL → Honeycomb; chat-only incomplete.

---

## 11. Where to read next

| Want | Open |
| --- | --- |
| Thinking rules | `references/META-001-meta-principles.md` |
| Identity ADR | `decisions/adrs/ADR-004-catalog-over-heuristics.md` |
| Atelier ARCH | `decisions/architecture/ARCH-004-salon-synthesize-atelier.md` |
| Runtime | `src/aulos_skills/runtime.py` |
| Thicken engine | `facet_classifier.py`, `dimension_templates.py`, `unknown_case_thicken.py`, `catalog_craft_floor.py` |
| Graduate | `promote_*.py` |
| Gates | `process_scorecard.py`, `product_scorecard.py`, `chamber_contracts.py`, `decontam.py` |
