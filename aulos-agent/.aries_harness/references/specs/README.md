---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "pipeline-specs-readme"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T10:55:22Z"
effective_status: "active"
effective_since: "2026-07-25T10:55:22Z"
content_fingerprint: "sha256:ab160f26181234c48ddf5eae835a4cb8eb389757b1698679feb262ff525dabf1"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Specification Packages

Use this directory for living behavior and acceptance contracts that translate request intent into clear engineering scope.

## Semantic role

- spec artifacts own what behavior, scope, acceptance, and quality constraints must hold
- they bridge request framing into domain, architecture, and story work
- they should not become the live task queue or the run-evidence surface

## Recommended naming

- `SPEC-*`
- `spec-package-*`
- `scope-*`

## Belongs here

- target behavior and explicit scope boundaries
- acceptance conditions and out-of-scope notes
- NFRs and rollout or migration edges
- owner, status, and linked downstream slices

## Keep out

- full business-case restatement from the request brief
- live backlog ownership or task sequencing
- test execution logs, GitHub delivery notes, or deployment evidence

## Trace links

- upstream request briefs and business asks
- downstream story packs, domain packages, architecture packs, and ADRs when needed

## Layer rule

- this directory belongs to `MetaDefineLayer`
- keep live execution notes and test logs out of specification packages
