---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:f2b5d3847d30fb619520564f6626bf3c8f47e12cfa6e84510017f43b915054b7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-003 — Salon Codex content model

## Intent

Treat a listening guide as a **Salon Codex**: a composed object with fixed chambers, filled first from curated corpus, then optionally enriched by live research/LLM under source hygiene.

## Chambers (canonical order)

| # | Chamber | Job |
| --- | --- | --- |
| 0 | Portal | Brand-adjacent title, catalog no., one listening thesis |
| 1 | Portrait | Composer oil portrait + credit + short life temper |
| 2 | Genesis | When/where/publication/patronage; myth vs document |
| 3 | Oeuvre & history | Status in composer’s catalog + music-historical stake |
| 4 | Immortality | Why this work remains a monument (specific reasons) |
| 5 | Anatomy | Form, deep-dives, listening map with ear actions |
| 6 | Sound world | Period instrument/ensemble + modern modes |
| 7 | Kindred | Related works with *why listen next* |
| 8 | Listening room | Famous interpretations by era/philosophy |
| 9 | Media shelf | YouTube appreciation + Discogs vinyl/masters |
| 10 | Practice path | Multi-evening listening drills |
| 11 | Caveats | Legends labeled; uncertainty visible |

## Data ownership

- **Corpus YAML** is the gold source for flagship works (offline excellence).
- **Width skill** owns Chambers 2–4, 7, 11 (+ reception).
- **Depth skill** owns Chambers 5–6, 10.
- **Compose skill** owns Portal + HTML assembly of all chambers.
- **Eval skill** scores specificity, ear-actionability, hygiene, chamber coverage, craft.

## Visual language

Concert-stage Aulos tokens: dark stage, warm parchment accent, Fraunces display + Manrope body. Portrait is a real visual anchor (oil painting), not a decorative gradient. No purple glow, no cream-terracotta brochure cliché, no card grid hero.

## Cold path

Works without corpus still get the same chamber *skeleton*, with honest “pending enrichment” copy rather than fake specificity.
