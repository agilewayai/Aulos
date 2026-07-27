---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "task-stack"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T16:20:00Z"
content_fingerprint: "sha256:c3f7ed7529d3e357f0d82d70c333e379f5de4662ae280fd45cadaee90317c431"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Task Stack

## Now

- AUDIT-009 F2/F3/F10/F11 closed in code; F1 deferred to operator secret rotation.
- API gate: `cd aulos-api && .venv/bin/pytest -q` → 94 passed.
- SPEC-009 decontam + family evidence gate shipped (Brahms Op.77 regression green)
- Keep SPEC-first + TDD on next listening-product slice (open RUN-* first)

## Next

- Catalog slot for Brahms Violin Concerto Op.77 (and other frequent Discogs cold works)
- Deeper F10: split `listening_guide.py` / `runtime.py` / remaining ops App tabs when next touched
- Adopt formal RUN-* template for every compose/eval behavior change

## Later

- Encryption-at-rest for `SystemSetting` secrets (post Sprint-1; see ADR-008)
- Align consumer facility layout with upstream `aries-harness-skills` docs if they add `.aries_harness/scripts` packaging
- Richer observability and production rollout

## Blocked

- (none for local iteration; F1 live rotation optional/deferred)
