---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "managed-doc"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:9ec33353553beb3430c7c1a84c8815649e92be58d5044a53f849819ca466809d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evolution cycle — Ambient media + identity hygiene → durable gates

date: 2026-07-25
source_findings:
  - Beethoven blob lacked ambient/bilingual vs Goldberg capability
  - Media `attachment` + origin-first + iframe sandbox blocked playback
  - LLM/RAG Goldberg chambers leaked into cello cold path
  - Eval could pass without ambient

## Promotion targets

| Finding | Durable asset | Status |
| --- | --- | --- |
| Silent chamber-only guides | SPEC-006 + eval hard-fail + compose SKILL | done |
| CDN / disposition breakage | SPEC-006 + `tests/test_media.py` inline assert | done |
| Flagship identity hijack | synthesize SKILL 0.2 + scrub + runtime tests | done |
| Studio srcDoc playback | SPEC-006 studio surface notes + web sandbox/base | done |
| Lessons stay in chat | insights.md + AGENTS + operating-defaults | done |

## Before → after (measured)

| Metric | Before | After |
| --- | --- | --- |
| `test_listening_chain_beethoven…` ambient needles | absent | required |
| `test_synthesize_scrubs_goldberg…` | n/a | new pass |
| `test_eval_hard_fails_without_ambient` | n/a | new pass |
| Media `Content-Disposition` | attachment | inline |
| Live #17 Goldberg leak | present | scrubbed |

## Next-run behavior change

Future agents reading AGENTS / operating-defaults / SPEC-006 will treat ambient + identity
hygiene as release gates, not optional polish.
