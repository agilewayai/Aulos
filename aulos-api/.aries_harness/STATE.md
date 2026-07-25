---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:9c026be0bce78b08d23dfa81019f63941489119cb24430ac7c3bbefea8a17121"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- STORY-PACK-008 `/discogs` release → listening guide (longrun RUN-008-DISCOG-001)

## Current phase (prior)

- Auth MVP + web research / locale closeout

## Active run

- RUN-008-DISCOG-001

## Hot facts

- `/discogs #release-id` parses in skills; API fetches Discogs release (master fallback), analyzes credits, seeds vinyl/interpretations, runs full 导赏 chain
- Env: optional `AULOS_DISCOGS_TOKEN` or `AULOS_DISCOGS_KEY`+`SECRET`
- Live: https://aulos.purezen.ai · https://aulos-ops.purezen.ai

- Project root: `aulos-api/`
- Role: API gateway
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-knowledge, aulos-skills

## Open risks

- Cross-service contract drift between web, api, mcp, and agent
- Live upstream backends unverified in Sprint-0
