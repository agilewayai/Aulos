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
content_fingerprint: "sha256:0abb195e2d1e6e1febe2f05665f04ec91d43a5cf44437566cf2e50e051c94983"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- REQ-011 / SPEC-021Δ diary guide lifecycle (revise / unpublish / delete) shipped locally
- REQ-010 Listening diary + plaza SNS S1–S6 + lifecycle delta (await deploy)

## Current phase (prior)

- REQ-010 / SPEC-019/020 Listening diary + plaza SNS (RUN-010 active)

## Active run

- idle (RUN-010 S1–S6 + REQ-011 lifecycle complete)


## Hot facts

- `/discogs #release-id` parses in skills; API fetches Discogs release (master fallback), analyzes credits, seeds vinyl/interpretations, runs full 导赏 chain
- Studio picker: `GET /v1/discogs/search?q=` autocomplete (auth)
- Env: optional `AULOS_DISCOGS_TOKEN` or `AULOS_DISCOGS_KEY`+`SECRET`
- Live: https://aulos.purezen.ai · https://aulos-ops.purezen.ai

- Project root: `aulos-api/`
- Role: API gateway
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-knowledge, aulos-skills

## Open risks

- Cross-service contract drift between web, api, mcp, and agent
- Live upstream backends unverified in Sprint-0
