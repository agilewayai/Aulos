---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T17:25:00+00:00"
generated_at: "2026-07-27T10:25:25+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:25+00:00"
content_fingerprint: "sha256:03b3fa3a9ca620f9cd1d90cf1b4ac3bf67c976a930f439312479e5aa56efe3e5"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-27T10:25:25+00:00`

## Recent changes

- Media durability: artifacts root → `data/persist/artifacts` (json + media/image|audio|meta)
- Wikidata P18 portraits + Commons PD audio; MusicBrainz recording/release meta + Cover Art images
- media_assets table + OPS media list; backup packs media blobs; Bach sample: 3 images + 2 meta on disk
- Docker durability: switched PG/Redis from named volumes → host bind mounts under `data/persist/`
- Redis AOF+RDB dual persistence; postgres `stop_grace_period=60s`; backup + persist_smoke scripts
- Verified: force-recreate and `compose down`/`up` keep composers=10 docs=55

## What is working

- Media durability: artifacts root → `data/persist/artifacts` (json + media/image|audio|meta)
- Wikidata P18 portraits + Commons PD audio; MusicBrainz recording/release meta + Cover Art images
- media_assets table + OPS media list; backup packs media blobs; Bach sample: 3 images + 2 meta on disk
- Docker durability: switched PG/Redis from named volumes → host bind mounts under `data/persist/`

## What needs attention

- working tree is dirty with 90 tracked or untracked change(s)
- verification gates are not documented yet in EVAL.md
- no explicit next-up slice is recorded

## Durable reminders

- no durable reminders recorded

## Promotion rule

- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset
- do not let retrospective output become the only place where important operating knowledge lives
