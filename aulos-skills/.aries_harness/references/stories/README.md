---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "pipeline-stories-readme"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:05Z"
content_fingerprint: "sha256:ce8025d72574111826c8cf374b9b6d30ab499deb60b7d92c41f0b34dd910222b"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Story Slice Packs

Use this directory for thin delivery slices that turn request and spec truth into verification-aware increments.

## Semantic role

- story artifacts own the current or next sprintable increment
- they tie user or operator value to acceptance, verification, dependencies, and touched design surfaces
- they should not restate the whole request brief or whole-system contract

## Recommended naming

- `STORY-*`
- `story-slice-*`
- `epic-*`

## Belongs here

- slice boundaries and why this slice matters now
- acceptance anchors and verification plan
- dependencies and touched design artifacts
- owner, status, and linked upstream artifacts

## Keep out

- full request-level business framing
- full spec-level behavior contract
- test execution logs, GitHub delivery notes, or deployment evidence

## Trace links

- upstream request and spec artifacts
- downstream design, code, tests, and delivery evidence

## Layer rule

- this directory belongs to `MetaDefineLayer`
- keep the live working queue in `TASK_STACK.md`, not here
