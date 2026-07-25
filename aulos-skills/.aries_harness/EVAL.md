---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "evaluation"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "CKPT-005"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T16:10:00Z"
content_fingerprint: "sha256:f7cfec5cb1055aad6c98af5bf8d777b476cc6cb60502220c8128e351214ce1d7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- unit (skills): `cd aulos-api && .venv/bin/python -m pytest ../aulos-skills/tests/test_runtime.py ../aulos-skills/tests/test_ambient_agent.py ../aulos-skills/tests/test_ambient_playlist.py -q`
- unit (media API): `cd aulos-api && .venv/bin/python -m pytest tests/test_media.py -q`
- media smoke: `curl -sI 'http://127.0.0.1:5090/v1/media/audio?src=<urlencoded-commons-url>&mode=cache' | grep -i content-disposition` → must contain `inline`
- live parity: recompose Goldberg + one cold-path Chinese work; assert bilingual + ambient in `guide_html`

## Acceptance notes

Minimum gate for listening compose/eval:

1. Salon Codex chambers present (composer / anatomy / practice / map).
2. Bilingual panes when `zh` pack exists (`data-lang="zh"` + `data-lang="en"`).
3. Ambient player present (`id="aulos-ambient"`); eval **fails** without it.
4. No foreign flagship leak (Goldberg markers absent from non-Goldberg works).
5. Media served `inline` via `/v1/media/audio` (cache preferred).

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
- checkpoint: `checkpoints/CKPT-005-ambient-identity-gates.md`
- insights: `docs/insights.md`
