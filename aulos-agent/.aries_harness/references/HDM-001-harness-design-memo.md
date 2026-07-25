---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "managed-doc"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:24b0068b8ff3690fad44d4be15e54cc3db1c85dba9c5bc396c5b8edb9181ecdf"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Harness Design Memo

## Artifact header

- Artifact ID: HDM-001
- Artifact type: harness-design-memo
- Status: active
- Owner: ubuntu
- Canonical path: `.aries_harness/references/HDM-001-harness-design-memo.md`
- Source of truth: this file
- Upstream links: REQ-001
- Downstream links: EC-001, ARCH-001
- Verification state: accepted-for-bootstrap
- Last reviewed: 2026-07-25
- Next review / refresh trigger: multi-agent or longrun expansion

## Runtime links

- Run ID: RUN-BOOTSTRAP-001
- Task ID / Slice ID: STORY-001
- Checkpoint ID: n/a
- Approval Request ID: n/a
- Trace ID: n/a
- Eval Report ID: n/a
- Audit Log ID: AUDIT-001

## Target frame

- Outcome: governed LangChain agent sub-project ready for feature slices
- Scope boundary (in / out): in = single-agent LangGraph package + harness; out = deploy/UI/multi-agent
- Constraints: Python, LangChain ecosystem, aries default layers
- Completion test: offline verification green and artifacts linked in REG-001

## Base loop

- Loop shape: Inspect / Plan / Edit / Verify / Summarize
- Verification rung expected per slice: unit + import smoke first; live LLM later
- Summarize trigger and durable record: JOURNAL.md + history-refresh

## Minimum artifacts

- Execution card: EC-001
- Playbook or workflow doc: RUNBOOK.md + README.md
- Where the runtime-artifact contract is exposed: EC-001 / REG-001 headers

## Layer choices

- Aries layers in use and why: core, context (light), request-to-architecture, coding-loop, observability (hooks only), policy (approval notes in mission)
- Routing boundaries between them: design artifacts before code; verify before closeout
- Pairing / handoff triggers: STORY-001 complete → history-refresh + review

## Assumptions and reuse

- Reusable assumptions: project root is `aulos-agent/`; package name `aulos_agent`
- What makes this harness reusable by another agent or operator: INDEX + REG + EC + ARCH readable without chat
- Open design questions: default provider for hackathon demos
