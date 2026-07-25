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
content_fingerprint: "sha256:d179b41e0881f89a0b20eda9a27bd6e2b4fd9e6009f61a3154f738754b4a931a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Artifact Register

## Artifact header

- Artifact ID: REG-001
- Artifact type: artifact-register
- Status: active
- Owner: ubuntu
- Canonical path: `.aries_harness/references/REG-001-artifact-register.md`
- Source of truth: this file
- Upstream links: REQ-001
- Downstream links: TRACE-001
- Verification state: bootstrap
- Last reviewed: 2026-07-25
- Next review / refresh trigger: after STORY-001 closeout

## Runtime links

- Run ID: RUN-BOOTSTRAP-001
- Task ID / Slice ID: STORY-001
- Checkpoint ID: pending
- Approval Request ID: n/a
- Trace ID: pending
- Eval Report ID: pending
- Audit Log ID: AUDIT-001

| Artifact ID | Type | Canonical path | Owner | Phase | Status | Verification state | Last reviewed | Source of truth | Refresh trigger | Runtime links | Upstream links | Downstream links |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | request | references/requests/REQ-001-langchain-agent-bootstrap.md | ubuntu | intake | active | accepted-intent | 2026-07-25 | file | product goal change | RUN-BOOTSTRAP-001 | n/a | SPEC-001 |
| SPEC-001 | spec | references/specs/SPEC-001-langchain-agent-runtime.md | ubuntu | shaping | active | draft-accepted | 2026-07-25 | file | runtime contract change | RUN-BOOTSTRAP-001 | REQ-001 | STORY-PACK-001, ARCH-001 |
| STORY-PACK-001 | story-pack | references/stories/STORY-PACK-001-agent-bootstrap.md | ubuntu | sprint | active | in_progress | 2026-07-25 | file | slice complete | STORY-001 | SPEC-001 | ARCH-001 |
| ARCH-001 | architecture | decisions/architecture/ARCH-001-langchain-agent-architecture.md | ubuntu | design | active | accepted | 2026-07-25 | file | topology change | RUN-BOOTSTRAP-001 | SPEC-001 | ADR-001 |
| ADR-001 | adr | decisions/adrs/ADR-001-langgraph-runtime.md | ubuntu | design | accepted | accepted | 2026-07-25 | file | orchestration change | RUN-BOOTSTRAP-001 | ARCH-001 | STORY-001 |
| TRACE-001 | traceability | references/TRACE-001-value-traceability.md | ubuntu | shaping | active | bootstrap | 2026-07-25 | file | slice ship | RUN-BOOTSTRAP-001 | REG-001 | STORY-001 |
| EC-001 | execution-card | references/tasks/EC-001-bootstrap-execution-card.md | ubuntu | execution | active | running | 2026-07-25 | file | slice close | RUN-BOOTSTRAP-001 / STORY-001 | STORY-001 | verification |
