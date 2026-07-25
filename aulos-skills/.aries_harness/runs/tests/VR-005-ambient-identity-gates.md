---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "test-execution"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:f27363a458eead9485f00da34157f13bd72077e429dfd231d7f92b81010f887e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# VR-005 — Ambient media + identity hygiene gates

date: 2026-07-25
related: CKPT-005, SPEC-006, REQ-005

## Commands

```bash
cd /home/ubuntu/hackathon/aulos/aulos-api
.venv/bin/pip install -e ../aulos-skills -q
.venv/bin/python -m pytest \
  ../aulos-skills/tests/test_runtime.py \
  ../aulos-skills/tests/test_ambient_agent.py \
  ../aulos-skills/tests/test_ambient_playlist.py \
  tests/test_media.py -q
```

## Expected

- All tests pass
- Beethoven cold-path HTML contains ambient + ZH + no Goldberg markers
- Eval without ambient → `pass=false`
- Media cache response disposition contains `inline`
