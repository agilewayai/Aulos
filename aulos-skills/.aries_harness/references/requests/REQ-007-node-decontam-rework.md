---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T19:20:00+00:00"
effective_status: "active"
effective_since: "2026-07-26T19:20:00+00:00"
content_fingerprint: "sha256:ee6217832da46285361246b120acac8cd7007a869e5331ddae1dbac6aa467f58"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-007 — Per-node decontamination + rework

## Why now

Guide #44 (Brahms Violin Concerto Op.77) completed with massive shelf pollution:
Beethoven cello-duo chambers, Bach Suite I ambient, and `family:duo-cello-piano`
attached solely because composer token `brahms` scored ≥2 with **zero** instrument/form
evidence. Scrub only ran at synthesize and had empty `conflict_markers` (unknown work).

## Problem

- Family packs unlock on composer alone.
- Decontam is a single late scrub, not a gate after each skill node.
- Unknown / Discogs-cold works have no `conflict_markers`, so foreign chambers pass through.

## Outcome

1. Composer-scoped family packs require instrument **or** form evidence in the title/blob.
2. After each listening skill node (synthesize → compose), run a decontam validator.
3. On failure: scrub + bounded rework of that node (refuse wrong family / expand markers).
4. Failures recorded in context for chain_trace / eval.

## Non-goals

- Adding every Discogs work to the Catalog in this slice.
- Hardcoded per-work `elif` trees (catalog / markers remain data-driven).
