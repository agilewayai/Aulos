---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T08:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T08:00:00Z"
content_fingerprint: "sha256:cb810f7709e3a39c0ae1f1761f2fd699c5ca5bd3173809fdd297a96974259faf"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-012 — Multi-source person card aggregation + bilingual CN/EN

## Why now

Person cards for composers / performers / ensembles were resolving from a single
winner source (Discogs *or* Wikidata). That loses complementary facts (Discogs
portrait + Wikidata lifespan + Wikipedia encyclopedia text) and leaves cards
monolingual.

## Outcome

1. **Aggregate then unify** — pull from multiple registry-verified authorities,
   merge **field-by-field** with provenance (not winner-take-all).
2. **Bilingual card** — every card exposes `summary_en` / `summary_zh` and
   `display_name_en` / `display_name_zh`; UI can switch locales.
3. Missing locale is filled by **native encyclopedia text first**, else
   **faithful translation** of the other locale (marked `*_origin=translated`).

## Authority roles (v1)

| Source | Role | Preferred fields |
| --- | --- | --- |
| Local KB | Cache / identity | all previously merged |
| Discogs | Catalog profile | portrait, EN profile, namevariations, discogs id |
| Wikidata | Structured identity | QID, lifespan, labels EN/ZH, sitelinks |
| Wikipedia EN/ZH | Encyclopedia prose | summary_en / summary_zh, thumbnail |

## Famous identity lock

When `person_id` is an allowlisted `famous_composers` id, the seed **wikidata QID** and canonical
EN name are authoritative. Wikidata search / Discogs merge **must not** overwrite that QID with a
homonym or relative (e.g. Franz Xaver Mozart → Wolfgang Amadeus Mozart). Persist path reasserts the
seed QID and corrects name/lifespan when drift is detected (see REQ-010 Δ).

## Non-goals

- Free-web scrape outside registry
- Full composer dossier SPARQL on every click
- Human proofreading workflow (quarantine docs still apply per tier)

## Links

- SPEC-012-person-multi-source-bilingual
- ADR-007-person-field-merge
- Extends REQ-011 / SPEC-011 (strict identity preserved)
