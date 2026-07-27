---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T16:55:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:55:00Z"
content_fingerprint: "sha256:dcaf75dea5daf4b2caced2fec9fc4d55a773c54cea906c6cf0dbe4fcd020e24a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-003 — Studio Discogs AJAX picker

Upstream: listening studio composer (SPEC-001) + API SPEC-008 search delta.

## Behavior

1. Studio composer shows a **+** control beside the listening prompt.
2. Clicking **+** opens a small menu; **Search Discogs** reveals a search field.
3. Typing (≥2 chars) debounces (~280ms) and calls `GET /v1/discogs/search` (auth).
4. Matching releases list with thumb / title / catno · label · year.
5. Selecting a row fills `/discogs #{id}` and starts the existing listening-guide stream
   (composer → musicians / work / composers via Discogs metadata).

## Acceptance

- + / menu / picker visible in authenticated studio.
- Empty / short query does not call search.
- Pick triggers compose with `/discogs #` command.
- Escape / outside click closes the picker.

## Non-goals

- Multi-select; marketplace; editing Discogs data in-web.
