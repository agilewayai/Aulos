---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "checkpoint"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:a5b1ae2e671ee461f24e90bf70f8071f8ea93c6098edb656c215c8ac84b84f7a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# CKPT-004 — Cold-path Salon Codex synthesize

status: complete
date: 2026-07-25
related: REQ-004, ARCH-004, SPEC-004

## Delivered

- New domain skill `aulos-listening-synthesize` (composer cards + family scaffolds + LLM JSON merge)
- Chain: intake → corpus → synthesize → width → depth → compose → eval
- Multilingual intake for Beethoven cello sonatas/variations Chinese request
- API asks ops LLM for structured Salon Codex JSON (fallback to short note)
- Offline parity: Beethoven guide ~17k HTML with same chamber set as Goldberg ~20k

## Verify

```bash
cd aulos-skills && .venv/bin/python -m pytest tests/test_runtime.py -q
```
