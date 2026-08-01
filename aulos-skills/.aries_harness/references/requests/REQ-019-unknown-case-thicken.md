---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:15:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:15:00Z"
content_fingerprint: "sha256:b20f05be3e2b6436ea0778b28f3768b43280be5c4d8526b7d4a012ca8d1728c9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-019 — Unknown-Case Thicken Loop (mechanism, not asset lists)

## Problem

Catalog / family / craft YAML thicken only **known** works. Future Discogs and
natural-language guides are unknown — hardcoding per-work assets cannot scale.
Thickness must come from a **mechanism** that classifies, synthesizes under
contracts, and optionally promotes survivors into caches.

## Outcomes

1. **FacetClassifier** — title/message → instruments/forms/era + archetype_id
   without requiring Catalog `work_id`.
2. **FamilyArchetype floor** — parameterized bilingual Salon floor from archetype
   (reuse family pack when registered; else built-in archetype template).
3. **Unknown-path synthesize** — when no Catalog/craft hit, use archetype floor
   instead of empty generic scaffold.
4. **Promote dry-run** — when product would pass on an unknown identity-stable
   dossier, emit `promote_candidate` JSON (Catalog/craft draft) without writing
   production assets.

## Non-goals

- Auto-writing production Catalog/craft files in v1 (dry-run only).
- Blocking compose on knowledge crawl completion.
- Replacing IntentLock / chamber contracts.

## Acceptance

- Unknown title (not in Catalog) still yields bilingual floor + `archetype:` in
  `synthesize_source`.
- Promote candidate schema present under dry_run when gates allow.
- Tests: `tests/test_unknown_case_thicken.py`.
