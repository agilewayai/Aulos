---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:50:00Z"
content_fingerprint: "sha256:5957af7d7d980718247391fc36a065748c3f1ded4c32db3d81a722227b5a0bb8"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-021 — Dimensional thicken + generic promote-to-production

## Hard constraint (operator)

**System-level / higher-dimensional only.** Forbidden:

- Per-work Python branches (`if mendelssohn`, `if guide #50`)
- Hand-authored craft/Catalog YAML for a single repro as the “fix”
- Expanding coverage by enumerating famous works one-by-one as the engine

Allowed accelerators (caches): family packs, craft packs, Catalog records — but the
**engine** must classify facets → dimensional template → contracts → promote
pipeline so *any* unknown Discogs/NLP title thickens and can graduate.

## Outcomes

1. **Dimension templates** — Salon floor from `(instruments × forms × era)` voices;
   named family YAML is optional accelerator.
2. **Generic promote-to-production** — operator gate promotes *any* staged
   candidate → Catalog composer/work stubs (schema-driven) + production craft
   from staging; no work-name special cases.
3. **Encode anti-case rule** in META/insights so future slices cannot regress.

## Non-goals

- Auto-promote without operator action.
- Fleet backfill of historical famous works as a substitute for the mechanism.
- Replacing IntentLock / chamber contracts.

## Acceptance

- Tests prove two *different* non-Catalog identities graduate via the same
  pipeline (no work-specific code paths).
- `tests/test_dimensional_promote.py`
- EVAL SPEC-031
