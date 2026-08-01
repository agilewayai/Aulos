---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-status"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-08-01T20:59:01+00:00"
effective_status: "generated"
effective_since: "2026-08-01T20:59:01+00:00"
content_fingerprint: "sha256:cdf22b3cea384690ff809b82ad0a446018f85e07aed98bd54624d86767fc8d1e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Current Status

Generated at: `2026-08-01T20:59:01+00:00`

## Current phase

- SPEC-032 / REQ-022 Identity freeze + Catalog/facet hardening (anti-case) shipped

## Branch and workspace

- no branch or workspace details recorded
- git branch: main
- HEAD: `1d325d5` Ship knowledge discovery, dossier, and benchmark console; refresh fleet honeycomb.
- working tree: dirty
- change: `M` `aulos-agent/.aries_harness/INDEX.md`
- change: `M` `aulos-agent/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- change: `M` `aulos-agent/.aries_harness/history/DOC_TRACE.md`
- change: `M` `aulos-agent/.aries_harness/history/README.md`
- change: `M` `aulos-agent/.aries_harness/history/RETROSPECTIVE.md`
- change: `M` `aulos-agent/.aries_harness/history/ROADMAP.md`
- change: `M` `aulos-agent/.aries_harness/history/STATUS.md`
- change: `M` `aulos-agent/.aries_harness/history/TIMELINE.md`

## Current milestone

- no current milestone recorded

## Active tasks


## Blockers

- none recorded

## Last verification

- verification command: unit (skills): `cd aulos-api && .venv/bin/python -m pytest ../aulos-skills/tests/test_runtime.py ../aulos-skills/tests/test_ambient_agent.py ../aulos-skills/tests/test_ambient_playlist.py -q`
- verification command: unit (process scorecard): `cd aulos-skills && python -m pytest tests/test_process_scorecard.py -q`
- verification command: unit (identity hygiene / guide #48): `cd aulos-skills && python -m pytest tests/test_identity_hygiene.py -q`
- verification command: unit (external review round / SPEC-022): `cd aulos-skills && python -m pytest tests/test_external_review_round.py tests/test_review_targets.py tests/test_targeted_revise.py -q`
- verification command: unit (product-prose hygiene / SPEC-023): `cd aulos-skills && python -m pytest tests/test_prose_hygiene.py tests/test_external_review_hygiene.py -q`
- verification command: unit (craft raise / SPEC-024): `cd aulos-skills && python -m pytest tests/test_craft_raise.py -q`
- verification command: unit (knowledge thicken + ProductScorecard / SPEC-025): `cd aulos-skills && python -m pytest tests/test_knowledge_product_score.py tests/test_marker_boundaries.py -q`
- verification command: unit (systemic cold thicken / SPEC-026): `cd aulos-skills && .venv/bin/python -m pytest tests/test_systemic_cold_thicken.py -q`
- verification command: unit (family coverage / SPEC-027): `cd aulos-skills && .venv/bin/python -m pytest tests/test_family_coverage.py -q`
- verification command: unit (catalog craft + fleet dossier / SPEC-028): `cd aulos-skills && .venv/bin/python -m pytest tests/test_catalog_craft_coverage.py -q` ；`cd aulos-api && .venv/bin/python -m pytest tests/test_ensure_composer_dossiers.py -q`
- verification command: unit (unknown-case thicken / SPEC-029): `cd aulos-skills && .venv/bin/python -m pytest tests/test_unknown_case_thicken.py -q`
- verification command: unit (promote staging / SPEC-030): `cd aulos-skills && .venv/bin/python -m pytest tests/test_promote_staging.py -q` ；`cd aulos-api && .venv/bin/python -m pytest tests/test_promote_stage_api.py -q`
- verification command: unit (dimensional promote / SPEC-031): `cd aulos-skills && .venv/bin/python -m pytest tests/test_dimensional_promote.py -q` ；`cd aulos-api && .venv/bin/python -m pytest tests/test_promote_production_api.py -q`
- verification command: unit (media API): `cd aulos-api && .venv/bin/python -m pytest tests/test_media.py -q`
- verification command: media smoke: `curl -sI 'http://127.0.0.1:5090/v1/media/audio?src=<urlencoded-commons-url>&mode=cache' | grep -i content-disposition` → must contain `inline`
- verification command: live parity: recompose Goldberg + one cold-path Chinese work; assert bilingual + ambient in `guide_html`

## Next action

- Optional: regenerate multi-work Discogs probe guides after deploy to confirm IntentLock freeze + multi_work status in production.
- Optional: expand dimension **voice tables** and form_lock aliens from live Discogs facet histograms — still dimensional, never per-work craft.
- Optional: knowledge-plane auto-thicken after promote-production (composer stub → dossier job).
- Optional operator: rotate live secrets in `.run/host.env` when ready to redeploy (F1 deferred).
- Later: fleet-wide adversarial review + gateway-stage scorecards (phase 2).
- Later: deeper F10 splits (`listening_guide.py` / `runtime.py`) when product work touches those files.
