---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:00:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:00:00+00:00"
content_fingerprint: "sha256:766427c99ee6f97b6a2b57664f01a8efa01f53226153715e679827eed2840eca"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-008 — Discogs release → listening guide (`/discogs`)

## Objective mode

`functional_capability`

## Why now

Listeners often start from a physical/digital pressing identity (Discogs release id)
rather than a catalogued work title. Aulos should accept that entry point, recover
work / composer / performers, then expand into a full 导赏.

## Problem

Studio intake only understands free-text work intent. There is no slash command that
resolves a Discogs record id into Catalog identity and the listening-guide chain.

## Outcome

- Operator enters `/discogs #release-id` in the listening studio.
- System fetches Discogs metadata, analyzes work / composer / performers / label notes.
- System expands into the normal Salon Codex listening guide for that work, seeded with
  this release as the primary interpretation / vinyl shelf entry.
- Catalog remains identity authority; Discogs never invents `work_id`.

## Constraints

- No composer/work hardcoding in Python.
- Locales remain `en` / `zh-Hans` / `zh-Hant` only.
- Discogs credentials optional via env (`AULOS_DISCOGS_TOKEN` or key/secret); unauthenticated
  low-tier allowed with clear failure messaging.
- Compliance: official Discogs API only — no HTML scrape of discogs.com.

## Non-goals

- Full Discogs label catalog crawl or marketplace features
- IMSLP connector
- Replacing Catalog with Discogs as identity source
- Persisting entire Discogs dump into the knowledge plane (later TASK_STACK)

## Links

- Downstream: SPEC-008, STORY-PACK-008, CKPT-008
- Cross: aulos-skills SPEC-008 identity; aulos-knowledge TASK_STACK Discogs connector (later)
