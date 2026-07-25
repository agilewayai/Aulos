---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "iteration-report"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T18:52:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T18:52:58+00:00"
content_fingerprint: "sha256:819b80864551c863d711817f256d57dd972cb8c2b440f2e0b33c7de11c692174"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evolution cycle — 2026-07-26 locale + intake + search enabler

## Source findings

1. Operator: open-source must not contain regional locale abbreviations in source.
2. Operator: "Unknown composer" despite clear 《书名》 / composer in the ask.
3. Operator: install Agent Reach as audited search enabler (not full social CLI).

## Promotion targets

| Finding | Durable asset | Gate |
| --- | --- | --- |
| Locale Hans/Hant only | `i18n.py`, `guide_render.py`, MEMORY, insights, AGENTS | `test_intake_i18n.py` |
| Intake composer recovery | `intake_parse.py`, catalog Dumky, runtime compose | `test_identity.py`, `test_intake_i18n.py` |
| Agent Reach fence | `skills/enabler-agent-reach/`, web_search deepen | `test_registry.py`, `test_web_research.py` |

## Before / after

- Before: single `zh` pane; Unknown composer on Dumky CN ask; no Agent Reach enabler.
- After: 简体|繁体|English; Dumky resolves to Antonín Dvořák; enabler layer installed + Jina deepen.

## Status

Promoted 2026-07-26 — history-refresh + well-organized completed fleet-wide.
