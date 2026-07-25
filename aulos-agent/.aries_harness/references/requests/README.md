---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "pipeline-requests-readme"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T10:55:22Z"
effective_status: "active"
effective_since: "2026-07-25T10:55:22Z"
content_fingerprint: "sha256:22c927c5ee418ca2cb634d5e409d51fc85058248f0cd2501cccf0e4b987648a9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Business Requirements

Use this directory for upstream request briefs that define why a piece of work matters, who it serves, and the business boundary around the ask.

## Semantic role

- request artifacts own business intent, target outcome, constraints, and non-goals
- they can point to success signals and acceptance intent, but not detailed system behavior
- they should stay upstream enough to guide shaping without becoming a sprint plan

## Recommended naming

- `REQ-*`
- `BRD-*`
- `requirement-*`

## Belongs here

- problem statement and why now
- intended outcome and business value
- constraints and non-goals
- source, owner, and status

## Keep out

- detailed actor or system behavior
- story-by-story sequencing or backlog control
- test execution logs, GitHub delivery notes, or deployment evidence

## Trace links

- upstream inputs such as stakeholder asks, research, or support themes
- downstream artifacts such as spec packages, story packs, and design work

## Layer rule

- this directory belongs to `MetaDefineLayer`
- keep live execution traces and logs out of this directory
