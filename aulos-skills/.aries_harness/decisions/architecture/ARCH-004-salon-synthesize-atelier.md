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
content_fingerprint: "sha256:557d08fc58295d56db577ff79459fb71643561e5bafc95d24d66245992f15f52"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-004 — Salon Codex synthesis atelier

## Chain

```
route → intake → corpus → synthesize → width → depth → compose → eval
```

## Compounding model

| Layer | Source | Role |
| --- | --- | --- |
| Work corpus | `aulos-listening-corpus` | Flagship offline excellence (Goldberg…) |
| Composer card | `aulos-listening-synthesize/assets/composers/` | Portrait, life, oeuvre/history voice |
| Family scaffold | `aulos-listening-synthesize/assets/families/` | Instrumentation + form listening pattern |
| LLM dossier | API ops LLM → structured JSON | Work-specific anatomy, interpretations, media |

Merge precedence (later wins on scalar prose; lists union with de-dupe):

`family → composer → corpus (if any) → llm_dossier`

## Synthesize skill contract

- Trigger: `listening.synthesize`
- Inputs: intake fields, optional `corpus_dossier`, optional `llm_dossier` / `llm_enrichment`
- Outputs: `corpus_dossier` (filled), `synthesize_hit`, `synthesize_source`

Width/depth treat a synthesized dossier like a curated one when Salon Codex fields exist.

## Intake

Must strip EN/ZH guide-request boilerplate and recognize composer + medium + form families.
