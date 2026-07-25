---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "harness-audit"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:45:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:45:00+00:00"
content_fingerprint: "sha256:37a84e8ae8f8ea386b8517656db6306c8852c40f72a81fb0340553d2ab9af815"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# AUDIT-008 — Deep review: `/discogs` story + OPS token

## Artifact header

- Artifact ID: AUDIT-008
- Artifact type: harness-audit
- Status: complete
- Owner: ubuntu
- Canonical path: `.aries_harness/runs/reviews/AUDIT-008-discogs-deep-review.md`
- Source of truth: live code + REQ/SPEC/STORY/CKPT-008 + Bugbot
- Upstream links: REQ-008, SPEC-008, STORY-PACK-008, CKPT-008, HOLD-008
- Downstream links: remediation list below
- Verification state: reviewed; not signed off
- Last reviewed: 2026-07-25T19:45:00Z
- Next review / refresh trigger: after F1–F3 fixed + live `/discogs` smoke

## Runtime links

- Run ID: RUN-008-DISCOG-001
- Task ID / Slice ID: STORY-PACK-008 (post-S4 review)
- Checkpoint ID: CKPT-008
- Approval Request ID: none
- Trace ID: n/a
- Eval Report ID: Bugbot (Discogs-focused); Security Review subagent **unavailable** (usage limit)
- Audit Log ID: AUDIT-008

## Review setup

- System / Harness: Aulos `/discogs` release → 导赏 + OPS Discogs token
- Reviewer: aries-harness-review + Bugbot
- Overall readiness: **conditional** — shippable for token config; slash-command path needs F1 before product signoff
- Remaining human gate: live studio smoke with real release id after F1; operator accept

## Evidence set

- Artifacts: REQ-008, SPEC-008, STORY-PACK-008, CKPT-008, HOLD-008, JOURNAL
- Code: `discogs.py`, `listening_guide.py`, `ops.py`, `intake_parse.py`, `aulos-ops` Discogs tab, `aulos-web` hint
- Verification: `pytest tests/test_discogs.py` → 5 passed (2026-07-25T19:45Z)
- Runtime: live OPS JS contains Discogs tab; `GET /v1/ops/discogs` → 401 (route present)
- Policy: superadmin-only OPS endpoints; token masked as `user_token_set`

## Findings

| Finding ID | Severity | Issue | Impact | Smallest practical fix | Evidence | Owner | Due date | Remediation status | Promotion target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | high | Malformed `/discogs` (no id) silently falls through to free-text compose | Listener gets wrong/empty guide instead of 400 | If message matches `/discogs` but parse fails → `DiscogsError(400)` | Bugbot; SPEC-008 Errors table; `discogs.py` resolve returns None | api | 2026-07-26 | open | coding-loop gate: test for `/discogs` alone → 400 |
| F2 | medium | Non-`DiscogsError` exceptions swallowed in `_run_chain_core` | Slash command stays as work title; CoT looks “done” but Discogs never ran | On any `/discogs` parse hit, wrap failures as `DiscogsError`/`502`; do not continue | `listening_guide.py:295-301` | api | 2026-07-26 | open | operating-defaults: never swallow slash-command failures |
| F3 | medium | Deploy/visibility process: UI/API shipped local-only; operator saw nothing | False “missing feature” signal; wasted cycle | Closeout checklist: build+restart+curl live JS/API before HOLD | Live pre-deploy: no Discogs in bundle; `/v1/ops/discogs` was 404 | fleet | 2026-07-26 | **mitigated** (redeployed) | harness closeout: “live evidence” required before hold |
| F4 | medium | Uncommitted Discogs stack (many `??` / dirty files) | Host can diverge from git; hard to resume | Commit + push after F1/F2 | `git status` shows untracked `discogs.py`, SPEC, tests | api | 2026-07-26 | open | policy: no HOLD without commit SHA in CKPT |
| F5 | low | Disabled-connector error says “LLM → Discogs”; UI is **Discogs** tab | Operator hunts wrong place | Update message to “OPS → Discogs tab” | `discogs.py:150-152`; Bugbot | api | 2026-07-26 | open | none |
| F6 | low | CKPT-008 stale (test counts, “set env token”, no OPS UI/deploy evidence) | Resume agents follow wrong next step | Refresh CKPT completed/verification/next-step | CKPT still says env-only + 4 tests | api | 2026-07-26 | open | longrun: CKPT refresh at deploy |
| F7 | low | No workflow step titled Discogs in CoT | Hard to see Discogs phase in studio trail | Emit optional early step `discogs` when slash used | `_run_chain_core` has no on_step for discogs | api | later | open | SPEC-003 step list delta |
| F8 | note | Token in `SystemSetting` plaintext JSON (same pattern as Brave) | DB dump exposes Discogs token | Accept for Sprint-1; document; later encrypt-at-rest | `save_discogs_config`; `public_*` masks | ops | later | accepted risk | policy: secrets-at-rest ADR |

## Coverage

- Target clarity: **good** — `/discogs #id` → analyze → 导赏
- Scope discipline: **good** — Label entity out of scope; Catalog owns identity
- Runtime alignment: **adequate** — RUN/CKPT present; Eval/Audit thin until AUDIT-008
- Routing boundaries: **good** — API fetch, skills parse, Catalog identity, OPS config
- Context hygiene: **adequate** — longrun hold note exists; CKPT stale (F6)
- Verification: **partial** — unit green; live slash smoke missing; F1 untested
- Observability: **weak** — no Discogs CoT step (F7); research.discogs in DB only
- Recovery: **adequate** — CKPT/HOLD resumeable after F6 refresh
- Human approval: **ok** — token is superadmin OPS; Discogs API read-only
- Reusability: **good** — REQ/SPEC/STORY templates usable
- Remediation closure: **this memo**
- Signoff closeout readiness: **not ready** until F1 (+ preferably F2, F4)

## Signoff recommendation

- Ready for reuse: **No** (block on F1)
- Ready for operator token config: **Yes** (OPS Discogs tab live after redeploy)
- Required follow-up: fix F1–F2; refresh CKPT; commit; live `/discogs #<id>` smoke
- Recommended next step: coding-loop remediation of F1/F2, then operator accept
