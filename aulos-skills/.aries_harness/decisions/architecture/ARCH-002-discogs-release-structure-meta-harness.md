---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T22:10:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:a9926452f9c73cf69c25e4259b57efa1c0e44cfa2c3f8d8685c1534700be8ea3"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-002 — Discogs release-structure meta harness

## Document control

- Architecture ID: ARCH-002
- Related: REQ-024, SPEC-034, ADR-006, META-001 §4.1, DOM-003, STORY-PACK-002
- Status: active (v1 scaffold shipped; pipeline hard-gate slices follow)

## Design drivers

| Driver | Note |
| --- | --- |
| Faithful album model | Classical LPs/CDs are often **programs**, not one work |
| Anti-thinness | Forbid family-scaffold deepen before program recognition |
| Agent-centric | API builds structure; Agent/skills expand per layer |
| Cross-identity | Tests use ≥2 unrelated pressings |

## Target control flow

```text
Discogs API (full release/master JSON)
        │
        ▼
aulos-api discogs.fetch + _parse_release_core
        │
        ▼
aulos_skills.release_structure.build_release_structure
        │  shape / program[] / structure_ready / expansion_plan
        ▼
┌─────────────────── GATE ───────────────────┐
│ assert_structure_ready — hard-fail if not   │
└───────────────────┬─────────────────────────┘
                    ▼
Layer 0  release_metadata (credits, formats, vinyl seed)
Layer 1  program_map frozen into IntentLock / research_json
Layer 2  PROGRAM DEEPEN LOOP (gateway g.program) — recursive per work:
            canonicalize titles (strip Discogs EN=DE=FR)
            for work in program[] (capped):
              q = program_search_query(catalog-first)  # not polyglot title
              force web cold_fill(q)
              LLM verify → on fail: web_search_raw floor (LLM is enrich, not gate)
              optional LLM enrich(q); else keep raw dossier
              collect program_iterations[]
            synthesize folds iterations → release-program-loop dossier
            (strip generic family map + junk bio hits)
Layer 3  pressing_synthesis (interpretations, comparative shelf)
                    ▼
compose / external review / product scorecard
```

Album-level `g.web` is **delegated** to the program loop when `multi_work_program`.

## Package layout

| Seam | Owner |
| --- | --- |
| Fetch + emit | `aulos-api` `services/discogs.py` |
| Structure domain | `aulos-skills` `release_structure.py` |
| Deepen orchestration | Agent + listening skills (STORY-PACK-002 slices) |
| Covenant | META-001 §4.1 |

## Quality attributes

- **Completeness** of Discogs payload before any LLM step
- **Traceability** — structure stored on analyze result, diary snapshot, kb_seed
- **Fail closed** — incomplete multi-work program must not ship thin family prose
- **Extensibility** — headings / index movements can refine clustering without case YAML

## Delivery slices

See STORY-PACK-002. This ARCH remains the living map as gates wire into runtime.
