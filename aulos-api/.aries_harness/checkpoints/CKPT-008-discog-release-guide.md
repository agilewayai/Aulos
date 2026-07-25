---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "checkpoint"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:00:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:00:00+00:00"
content_fingerprint: "sha256:6ace3b879f78f3bf166d9852de1b5fe7236914fa2a53c4c8a793bcf5651bcd1a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# CKPT-008 — Discogs `/discogs` longrun

## Artifact header

- Artifact ID: CKPT-008
- Artifact type: checkpoint
- Status: active
- Owner: ubuntu
- Canonical path: `.aries_harness/checkpoints/CKPT-008-discog-release-guide.md`
- Source of truth: REQ-008 / SPEC-008 / STORY-PACK-008
- Upstream links: REQ-008, SPEC-008
- Downstream links: `discogs.py`, `listening_guide.py`, `intake_parse.py`, web studio hint
- Verification state: verified (unit + regression); awaiting human acceptance / deploy
- Last reviewed: 2026-07-25T19:15:00Z
- Next review / refresh trigger: after live Discogs token smoke on staging

## Runtime links

- Run ID: RUN-008-DISCOG-001
- Task ID / Slice ID: S0–S3 done; S4 closeout
- Checkpoint ID: CKPT-008
- Approval Request ID: none
- Trace ID: n/a
- Eval Report ID: n/a
- Audit Log ID: n/a
- Checkpoint time: 2026-07-25T19:15:00Z
- Run / Slice: longrun STORY-PACK-008

## objective

Finish the story: slash command `/discogs #release-id` auto-analyzes the Discogs
record (work, composer, performers) and expands into a full Aulos listening guide.

## completed work

- REQ-008 / SPEC-008 / STORY-PACK-008 / CKPT-008
- `parse_discogs_command` in aulos-skills
- `aulos_api/services/discogs.py` fetch+analyze; master fallback
- `_run_chain_core` rewrite intent + kb_seed + `research.discogs`
- Web studio placeholder + `/discogs` example button
- Tests: `tests/test_discogs.py` 4 passed; `test_listening_guide.py` green; skills parse unit
- Command renamed `/discog` → `/discogs` (2026-07-25)

## in-progress work

- none (implementation complete; hold for operator deploy/acceptance)

## next step

Operator: set `AULOS_DISCOGS_TOKEN` in deploy env; smoke `/discogs #<real-release-id>` on studio; accept or request tweak.

## blockers / risks

- Without token, Discogs low-tier rate limits may 429 in production
- Credit role strings vary across classical releases

## verification performed

- `pytest tests/test_discogs.py` → 4 passed
- `pytest tests/test_listening_guide.py` → green
- `pytest tests/test_intake_i18n.py::test_parse_discogs_slash_command` → passed

## verification still needed

- Live Discogs API smoke with real token (approval-gated ops)

## context state

- pressure state: low
- chosen context op: continue → hold-state after signoff
- hot carry-forward set: SPEC-008, discogs.py, listening_guide seed path
- detail moved to summary / memory / archive: analyzer heuristics

## Workspace isolation

- Workspace root (agent writes confined here): `/home/ubuntu/hackathon/aulos`
- Write-scope boundary: aulos-api, aulos-skills, aulos-web (hint only)
- Host-repo isolation rule: stay under workspace root

## resume notes

- Do not reopen Label-entity browser scope
- For prod: prefer token auth; keep Catalog as identity authority
