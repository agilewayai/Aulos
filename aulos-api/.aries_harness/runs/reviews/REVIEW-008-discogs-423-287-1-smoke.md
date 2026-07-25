---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "review-memo"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:45:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:45:00+00:00"
content_fingerprint: "sha256:bdd667a19777419893286bcb74a2bbe5209d73aaf731525f652671681d282728"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REVIEW-008 — Real smoke `/discogs` for `423-287-1`

## Target

Real Discogs smoke of operator input resembling `423-287-1` (Horowitz Plays Mozart, DG).

## Smoke evidence

| Probe | Result |
| --- | --- |
| `parse_discogs_command("/discogs #423-287-1")` | **BUG** → `release_id=423` (truncates at first hyphen) |
| `GET /releases/423` | Wrong pressing (Besos De Los Angeles EP) |
| Discogs `catno=423-287-1` search | Hits Horowitz/Mozart DG releases (e.g. 4084139) |
| Analyze release 4084139 | Composer Mozart OK; performers incorrectly include Mozart; work_title is marketing blurb |

## Findings

| ID | Severity | Finding | Evidence | Measurable fix | Status |
| --- | --- | --- | --- | --- | --- |
| F1 | **blocker** | Parser only accepts pure digits; hyphenated catalog numbers become wrong release ids | `/discogs #423-287-1` → 423 | Unit: parse returns `catno=423-287-1`; smoke resolves Mozart/Horowitz | **fixed** |
| F2 | **blocker** | No catalog-number → Discogs search path | SPEC assumed release id only | Search `catno` then fetch release; test with fixture | **fixed** |
| F3 | medium | Composer listed in `artists` becomes a “performer” | Mozart in performers list | Exclude composer names from performers | **fixed** |
| F4 | medium | Work title stays marketing (“Horowitz Plays Mozart…”) instead of K.488 / K.333 | analyze output work_title | Prefer workish release/track titles | **fixed** |
| F5 | low | Seed copy still says `/discog` | interpretations.why_listen | Rename to `/discogs` | **fixed** |
| F6 | low | Deploy lag previously hid OPS UI | prior review | Redeploy after this fix | open → redeploying |

## Signoff recommendation

**Conditional pass** after host redeploy: live resolve smoke already OK locally (`release_id≠423`, Mozart + Horowitz/Giulini, work title K.488/K.333).

## Remediation owner

Coding-loop now (this run). Checkpoint: CKPT-008 update after verify.
