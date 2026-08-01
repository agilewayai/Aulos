---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T09:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T09:50:00Z"
content_fingerprint: "sha256:003aa2e528b03c2ec5fb515a04c8a0c0a51816d791facc057951e2dabfc6890e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-009 — Diary blog layout (calendar + tag cloud)

## Surfaces

- **Browse**: blog feed of own diaries + sticky aside (`calendar` month grid, `tag cloud`).
- **Compose / Reader**: existing Discogs compose + post editor remain; reader returns to filtered feed.

## Calendar

- Month navigation (prev / next / today).
- Day cell marks days with ≥1 post (`listened_on` else local date of `created_at`).
- Selecting a day filters the feed; selecting again clears (or explicit「全部」).

## Tag cloud

- Aggregate from list snapshots: composers, performers, ensembles, genres, styles, format (`source_kind`).
- Weight = occurrence count; font-size scales with weight.
- Click toggles filter; active tag highlighted; clear control.

## Data

- `GET /v1/listening-diary` must return `snapshot` (composers / performers / ensembles / genres / styles) for client aggregation.
