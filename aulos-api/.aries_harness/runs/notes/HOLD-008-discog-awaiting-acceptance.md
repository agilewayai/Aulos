---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "hold-state-note"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:15:00+00:00"
content_fingerprint: "sha256:dd2cda3f82d3210c2f100291bef73ff04fb1054bef9a0cb9a53b54835d6a42c6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# HOLD-008 — `/discogs` awaiting human acceptance

## Status

Implementation complete for STORY-PACK-008. Routine progress pings stopped.

## Waiting on

1. Deploy with optional `AULOS_DISCOGS_TOKEN` (recommended for rate limits)
2. Operator smoke: studio → `/discogs #<real-release-id>` → guide names work/composer/performers
3. Explicit accept / change request

## How to resume

- Checkpoint: `CKPT-008-discog-release-guide.md`
- Code: `aulos_api/services/discogs.py`, `listening_guide._run_chain_core`, `intake_parse.parse_discogs_command`
