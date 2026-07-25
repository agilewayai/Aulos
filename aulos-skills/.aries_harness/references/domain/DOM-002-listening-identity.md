---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "domain-analysis"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:01:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:01:00+00:00"
content_fingerprint: "sha256:ba130f56412d147266abe41a6c18299f6880712102981026bcac7bf9849118de"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# DOM-002 — Listening identity bounded context

## Ubiquitous language

| Term | Meaning |
| --- | --- |
| **Composer** | Person identity card (aliases, names). Not a work shelf. |
| **Work** | Catalogued composition identity (`work_id`). Authority for “what is being listened to.” |
| **Family** | Genre scaffold (e.g. solo-cello-suites) — structural listening template, not identity proof. |
| **Dossier** | Salon Codex long-form content for a work (may be absent on cold path). |
| **Conflict** | Another work whose distinctive markers must be scrubbed from this guide. |
| **Weak token** | Linguistic token that never proves same-work alone (`bwv`, `suite`, composer surnames…). |

## Bounded contexts

1. **Identity** (Catalog + Resolver) — confirms who/what.
2. **Research** (RAG / corpus dossier) — enriches after identity.
3. **Compose** (Salon HTML) — renders confirmed + scrubbed dossier.
4. **Ambient** — selects audio by `ambient_ref` or facets of confirmed identity.

## Invariants

- Composer ≠ Work. Bach card must not imply Goldberg.
- RAG similarity ≠ identity. No `kb_dossier` without identity match.
- Positive and negative identity travel together (`distinctive_tokens` + `conflict_work_ids`).
- Uncertain provenance fields remain marked uncertain — never filled with lore-as-fact.

## As-is vs to-be

| As-is | To-be |
| --- | --- |
| Intake `elif` trees per flagship | Catalog-driven Resolver |
| Scrub hardcoded Goldberg/Beethoven markers | Markers derived from conflict works |
| Sparse Goldberg-only seed attracts all Bach queries | Catalog identity cards indexed; work_id gate |
