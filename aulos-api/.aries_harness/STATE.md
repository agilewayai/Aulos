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
content_fingerprint: "sha256:68be7a27cf7d96481518237be7d85c09bc989ab9a09daea5bb10e505ae0db52d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- SPEC-034 Slice F deployed: Discogs program composer propagation +
  failed-guide persistence/publish gate verified and published to production;
  guide #59 live recompose remains pending
- REQ-011 / SPEC-021Δ diary guide lifecycle (revise / unpublish / delete) code
  deployed with the 2026-08-02 host deploy; dedicated feature smoke not rerun
- REQ-010 Listening diary + plaza SNS S1–S6 + lifecycle delta code deployed
  with the 2026-08-02 host deploy; dedicated feature smoke not rerun

## Current phase (prior)

- REQ-010 / SPEC-019/020 Listening diary + plaza SNS (RUN-010 active)

## Active run

- Closed + deployed: SPEC-034 Slice F guide #59 gateway/persist gate
  (2026-08-02); live guide #59 recompose pending
- Closed: SPEC-034Δ gateway `g.program` deepen loop + web partial (2026-08-01)
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
