---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "story-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:00:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:00:00+00:00"
content_fingerprint: "sha256:85ca64465bfc61951ef37718618458784e17b7c545f3c43a00ad6e6cd623fefb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# STORY-PACK-008 — `/discogs` release guide (longrun)

Upstream: REQ-008, SPEC-008  
Checkpoint: CKPT-008  
Mode: longrun + coding-loop

## Slices

| ID | Intent | Verify first | Status |
| --- | --- | --- | --- |
| S0 | Harness artifacts (REQ/SPEC/STORY/CKPT/STATE/TASK) | Checkpoint contract sections present | **done** |
| S1 | Parse `/discogs` + Discogs client + analyzer (mocked) | `pytest tests/test_discogs.py` | **done** |
| S2 | Wire into `_run_chain_core` + seed dossier; skills parse helper | `pytest tests/test_discogs.py tests/test_listening_guide.py` + skills intake tests | **done** |
| S3 | Web studio hint + EXAMPLE for `/discogs` | web typecheck/build if touched | **done** |
| S4 | Closeout: JOURNAL, history-refresh, hold/signoff | memory-inspect + history STATUS | **done** (hold for deploy accept) |

## Cadence

- Progress every 30 minutes while coding
- Update CKPT-008 at each slice boundary
- Context op default: `continue`; compact if transcript noise rises

## Non-goals

- Label-entity browser
- Live Discogs token provisioning in OPS UI (env-only this slice)
