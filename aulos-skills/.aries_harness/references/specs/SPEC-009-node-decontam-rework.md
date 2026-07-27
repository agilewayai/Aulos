---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T19:20:00+00:00"
effective_status: "active"
effective_since: "2026-07-26T19:20:00+00:00"
content_fingerprint: "sha256:ae922028f17ca8f97d66f21cd4fdee860d34d6648e576ab1093104aa33a1c20c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-009 — Node decontam gate & family evidence

## Family match (delta to SPEC-004)

For a family pack whose `match.composers` is non-empty:

1. Composer must hit (blob or `composer_guess`) — existing rule.
2. **Evidence ≥ 1** from `match.instruments` ∪ `match.forms` tokens present in the
   title/message blob. Composer score alone must **not** unlock the pack.

Families without `match.composers` keep the prior threshold (instrument/form score ≥ 2).

## Marker resolution

Scrub / validate markers = context `conflict_markers` ∪ catalog-derived aliens:

- Known `work_id` → `Catalog.conflict_markers_for(work)`.
- Unknown work → distinctive tokens / catalog numbers / aliases (len≥5, non-weak) of
  catalog works whose composer does not match the locked shelf composer, plus the
  union of explicit `identity.conflict_markers` on all works. Drop markers that appear
  in the locked title/composer blob.

## Per-node gate

After `listening.synthesize`, `listening.width`, `listening.depth`, `listening.compose`:

1. Inspect node outputs (dossier chambers / guide HTML / ambient) against markers.
2. Extra synthesize check: if `synthesize_source` contains `family:` and family instruments
   do not intersect the title blob, treat as pollution (`foreign_family`).
3. On fail (max 1 rework):
   - Expand `conflict_markers` on context.
   - Set `refuse_families=true` when foreign family detected.
   - Re-run the same node executor; scrub before / after as needed.
4. If still polluted: set `decontam_failed=true` and findings on context; eval must soft-fail
   or hard-fail when HTML still carries alien markers.

## Acceptance

- Brahms Violin Concerto Op.77 (Discogs cold, no `work_id`) must **not** attach
  `family:duo-cello-piano`, must not render Beethoven cello-duo chambers or Bach Suite I
  ambient as the primary shelf atmosphere.
- Existing Beethoven cello / Bach cello / Mozart piano regression tests stay green.
- Chain context records `decontam_events` when a rework fires.
