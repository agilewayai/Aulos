---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "story-slice-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:1cb8b88576a69b79cda37b66c6ed4a53f8aab32c259e255983cd51ea60f49c2f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Story Slice Pack

## Semantic Role

- This artifact owns the thin increment that is about to be planned, implemented, or verified.
- It should connect one slice of value to acceptance, verification, dependencies, and touched design surfaces.
- It should not restate the full request brief or whole-system scope contract.

## Document Control

- Pack ID: STORY-PACK-001
- Artifact type: story-pack
- Objective mode: functional_capability
- Parent request: REQ-001
- Parent spec: SPEC-001
- Owner: ubuntu
- Current sprint or increment: Sprint-0 bootstrap
- Last reviewed: 2026-07-25
- Child refs: STORY-001
- Source of truth: `.aries_harness/references/stories/STORY-PACK-001-agent-bootstrap.md`

## Slice Overview

| Story ID | Story statement | User value | Acceptance anchor | Status | Linked design artifacts |
| --- | --- | --- | --- | --- | --- |
| STORY-001 | As an operator, I can install and run an offline-verified LangGraph agent skeleton so I can extend tools and prompts safely | bootstrapped agent workspace | pytest green + package layout matches ARCH-001 | done | ARCH-001, ADR-001 |

## Story Detail

### Story: STORY-001

- Story ID: STORY-001
- User story: As an operator, I can install `aulos-agent` and verify a LangChain-ecosystem agent skeleton offline so later features have a stable seam map.
- Slice type: feature
- Why this slice matters now: without a governed package + harness, later agent work will sprawl
- Acceptance criteria:
  - `.aries_harness/` present with request/spec/story/arch linked
  - `src/aulos_agent/` implements config, llm, prompts, tools, memory, graph, observability, cli
  - offline unit tests cover state, tools, and graph compile/invoke with FakeListChatModel or equivalent
  - README documents architecture and how to run
- Verification plan: `pytest -q`; import smoke; harness INDEX remains readable
- Before or after evidence expectation: verification report under `.aries_harness/runs/tests/`
- Domain artifacts touched: n/a (deferred)
- Architecture artifacts touched: ARCH-001
- ADR impact: ADR-001
- Release or rollout note: local-only
- Refresh trigger: package layout change
- Audit log entry: AUDIT-001

## Follow-on Slices

- Next likely slice: STORY-002 live provider invoke
- Deferred slice: STORY-003 durable checkpointer / store
