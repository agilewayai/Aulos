---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "engineering-pipeline"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:43Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:43Z"
content_fingerprint: "sha256:42ad1d07ef46993df1abef086866d1bbc5776d98feb8d3d4450ee8e318b7d3a0"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Engineering Pipeline

## Purpose

- keep the end-to-end engineering delivery line inspectable from business requirement to production deployment

## Current focus

- Current stage:
- Active iteration:
- Latest status:
- Next gate:

## Phase ledger

### 1. Business requirement description
- Status:
- Canonical directory: `references/requests/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 2. Domain analysis and modeling
- Status:
- Canonical directory: `references/domain/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 3. System design
- Status:
- Canonical directory: `decisions/architecture/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 4. Iteration planning
- Status:
- Canonical directory: `references/iterations/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 5. Task breakdown
- Status:
- Canonical directory: `references/tasks/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 6. Risk tracking
- Status:
- Canonical directory: `references/risks/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 7. Test execution and fixes
- Status:
- Canonical directory: `runs/tests/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 8. Iteration report
- Status:
- Canonical directory: `runs/reports/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 9. GitHub delivery
- Status:
- Canonical directory: `runs/github/`
- Active artifact:
- Verification or gate:
- Latest evidence:

### 10. Production deployment
- Status:
- Canonical directory: `runs/deployments/`
- Active artifact:
- Verification or gate:
- Latest evidence:

## Pipeline rules

- keep `MetaDefineLayer` truth in `MISSION.md`, `ADR.md`, `RUNBOOK.md`, `EVAL.md`, `RISKS.md`, `references/`, and `decisions/`
- keep `RunCookingLayer` process state in `TASK_STACK.md`, `PIPELINE.md`, `STATE.md`, `JOURNAL.md`, `checkpoints/`, and `runs/`
- keep shared support material in `README.md`, `INDEX.md`, `MEMORY.md`, `memory/`, `history/`, and `archive/`
- run `/aries-harness pipeline-inspect` before handoff, major review, GitHub delivery, or deployment
- run `/aries-harness well-organized` when extra Markdown appears in the root or the wrong collection
