---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:67bd6f8cf8394a95f67d2e03f3dae03f1addf2d35dfa4a13da4250612f8de433"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Request Brief

## Semantic Role

- This artifact owns why the work matters, for whom it matters, and the boundary around the ask.

## Document Control

- Request ID: REQ-001
- Artifact type: request
- Objective mode: functional_capability
- Title: Bootstrap aulos-web as the Aulos operator GUI
- Status: active
- Owner: ubuntu
- Review date: 2026-07-25
- Parent refs: n/a
- Child refs: SPEC-001, STORY-001, ARCH-001
- Source of truth: `.aries_harness/references/requests/REQ-001-aulos-web-bootstrap.md`

## Belongs Here

- Request source: operator ask to apply aries-harness and init `aulos-web`
- Problem statement: operators need a first-class web console instead of CLI-only interaction
- Why now: hackathon multi-service bootstrap; harness and seams must exist before feature work
- Intended user or operator outcome: a runnable, testable `aulos-web` skeleton that another operator can extend
- Business value: clearer separation of GUI / gateway / MCP / agent concerns
- Success signals: `.aries_harness/` initialized; starter app present; offline verify path; linked mission/architecture/stories
- Scope boundary: `aulos-web/` only for this request; contracts with siblings are documented but not fully productized
- Constraints: aries-harness governed artifacts; keep Sprint-0 offline-verifiable
- Non-goals: auth/SSO, production hosting, custom design system package, mobile native apps

## Delivery Links

- Spec package: SPEC-001
- Story-slice pack: STORY-PACK-001
- Architecture design pack: ARCH-001
- Value traceability matrix: TRACE-001

## Refresh Triggers

- What should force this brief to be reviewed: change of product role for `aulos-web` or merge into another service
