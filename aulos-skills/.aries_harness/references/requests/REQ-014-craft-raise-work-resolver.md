---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T18:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T18:50:00Z"
content_fingerprint: "sha256:810c1444585c9d28a7c42be3a878be63884ddc6570f1566864e67b965cac6123"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-014 — Raise craft: Work Resolver + chamber contracts + cold thicken

## Problem

SPEC-023 stopped product pollution. Guides can still be **thin**: empty portrait /
genesis / interpretations, ZH stub parity, Discogs cold path clearing Catalog
`work_id` / family floors. Defense ≠ craft.

## Outcomes

1. **Work Resolver** — packaging-cleaned Discogs / hint / message → Catalog
   `work_id` + `family_id` when possible; do not wipe identity on Discogs alone.
2. **Chamber contracts** — minimum EN craft + ZH parity before eval can pass on
   identity-resolved shelves.
3. **Cold thicken** — family / composer synthesize packs registered and applied as
   form floor; fill empty genesis / sound_world / map / width / ZH mirrors.
4. Product eval uses contract gaps (not only HTML chrome presence).

## Non-goals

- Full knowledge-plane crawl for every cold work in this slice.
- Replacing expert LLM review.
- Per-release case patches.

## Acceptance

- Resolver maps Songs Without Words packaging dump → `mendelssohn.lieder-ohne-worte`.
- Chamber audit fails empty map / missing ZH thesis when EN craft exists.
- Family `lyric-piano-miniatures` registered; Mendelssohn cold path ships non-empty
  genesis + map + ZH thesis after synthesize.
- Tests + guide #50 regen shows thicker atelier (atelier_hits / eval).
