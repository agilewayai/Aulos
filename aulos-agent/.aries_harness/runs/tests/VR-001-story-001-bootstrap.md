---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "test-execution"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:b77b57a4288de8d2acec23d489480090ebfefec3138d729b847f1a6c61503eed"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Verification Report — STORY-001 bootstrap

## Artifact header

- Artifact ID: VR-001
- Artifact type: verification-report
- Status: passed
- Owner: ubuntu
- Canonical path: `.aries_harness/runs/tests/VR-001-story-001-bootstrap.md`
- Upstream links: STORY-001, EC-001
- Verification state: passed
- Last reviewed: 2026-07-25

## Runtime links

- Run ID: RUN-BOOTSTRAP-001
- Task ID / Slice ID: STORY-001
- Eval Report ID: VR-001

## Checks

| Check | Result | Notes |
| --- | --- | --- |
| `pip install -e ".[dev]"` | pass | hatchling src layout |
| `pytest -q` | pass | 7 passed |
| `aulos-agent --show-config` | pass | provider=fake |
| `aulos-agent "hello"` | pass | fake model response |

## Residual risk

- Live OpenAI/Anthropic invoke not exercised (STORY-002)
- In-memory checkpointer only (STORY-003)
