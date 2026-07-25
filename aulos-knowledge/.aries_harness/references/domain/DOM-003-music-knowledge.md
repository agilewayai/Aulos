---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "domain-analysis"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:912eefa9cfbd8d6f5011fd4b9dc9672794c48245aa1921f138d27082e3c7baa6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# DOM-003 — Music knowledge domain

## Language

| Term | Meaning |
| --- | --- |
| SourceAuthority | Allowlisted external or internal origin of truth |
| Artifact | Immutable raw fetch evidence (bytes + hash) |
| Job | One crawl/import execution |
| Composer / Work / Recording | Professional entities (not Salon dossier prose) |
| KnowledgeDocument | Retrievable text unit linked to entities + provenance |
| Quarantine | Non-published holding state pending review |
| aulos_work_id | Link to product Catalog identity |

## Invariants

- Business User ≠ Knowledge Composer.
- Catalog identity confirmation ≠ encyclopedic content richness.
- No publish without provenance.
- License_class on source constrains what connectors may store.
