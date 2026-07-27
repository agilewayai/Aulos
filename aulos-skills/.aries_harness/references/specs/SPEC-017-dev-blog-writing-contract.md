---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T10:24:52+00:00"
effective_status: "active"
effective_since: "2026-07-27T10:24:52+00:00"
content_fingerprint: "sha256:42eeb5a442c9941877e29cdf4cff1c0e0bcd38f4bbdbd6561b50bed1a0405af6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Dev Blog — internal writing contract

Canonical voice and structure for Ops **Dev Blog** generation.

**Not for external publish.** Purpose: faithful **development trajectory** for the team.

## Rules (summary)

1. **Evidence-only** — git + harness; no fabrication.
2. **Factual tone** — no hype, emotion, or marketing render.
3. **Subsystem clarity** — say which part (`aulos-api`, `aulos-web`, `deploy`, …) changed.
4. **Honest impact** — if internal-only, say so.
5. **Three fixed sections** — see SPEC-017.

Full spec: [`aulos-api/.aries_harness/references/specs/SPEC-017-dev-blog-writing-contract.md`](../../aulos-api/.aries_harness/references/specs/SPEC-017-dev-blog-writing-contract.md)

Implementation: `aulos-api/src/aulos_api/services/dev_blog_contract.py`
