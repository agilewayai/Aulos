---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "domain-model"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T22:10:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:c30f9da4dda17beb8f51e1942484d75a4e30d708a4c30f557bf2c0e4950d3f02"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# DOM-003 — Discogs release structure domain

## Bounded context

**Release program modeling** — between Discogs connector fetch and listening
identity/thicken. Distinct from Catalog work identity (DOM-002): a release may
host many Catalog works.

## Ubiquitous language

| Term | Meaning |
| --- | --- |
| Release | Discogs release/master pressing with credits + tracklist |
| Program work | One catalogued (or heading-grouped) composition on the pressing |
| Shelf / shape | `single_work`, `multi_work_program`, `shelf`, `unknown` |
| Structure-ready | Enough metadata + coherent program to allow deepen |
| Expansion layer | Ordered deepen stage (metadata → map → per-work → pressing) |

## Entities

- `ReleaseStructure` (aggregate root for intake)
- `ProgramWork` (entity inside the aggregate)

## Invariants

1. No deepen without structure-ready when source is Discogs.
2. Multi-catalog pressings must expose ≥2 program works before family thicken.
3. Movements without catalogs do not invent false multi-work programs.
