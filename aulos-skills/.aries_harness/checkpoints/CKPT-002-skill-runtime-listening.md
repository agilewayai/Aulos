---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "checkpoint"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:75b561823929b31368f812b70d0c567b4adcf48f0258bed1938a0c34848c4c99"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Longrun Checkpoint — Skill-powered listening 1–4 (closeout)

schema_version: "0.1"
project_id: "aulos-skills"
runtime_ids:
  - aulos-skills
  - aulos-api
  - aulos-web
  - aulos-ops
  - aulos-mcp
objective: >
  Finish residual 1–4: Disable gates runtime; SSE progressive steps;
  web live trail; proxy streams event-stream.
completed_work:
  - SkillRuntime honors disabled_skill_ids (status=skipped)
  - API listening workflow + ops probe respect ops disabled set
  - POST /v1/listening-guides/stream SSE (event: step|done|error)
  - deploy/serve.py streams text/event-stream without buffering
  - aulos-web streamListeningGuide updates chain-of-thought live
  - Tests: disable skip + SSE + runtime iter
in_progress_work: []
next_step: Optional more corpus dossiers / SSE step.start heartbeat
blockers_risks: []
verification_performed:
  - aulos-skills pytest 7 passed
  - aulos-api listening+api tests green; full suite run at deploy
  - live SSE smoke on :5090 and proxy :5091
verification_still_needed: []
context_state: hold
chosen_context_op: continue
updated_at: "2026-07-25T13:40:00Z"
status: complete
