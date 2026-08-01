---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T11:31:00Z"
effective_status: "active"
effective_since: "2026-08-01T11:31:00Z"
content_fingerprint: "sha256:279f2c8402d794ecc27a3c3be5dd878ff1720de1c88d367b906bc1e31a5496ca"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-011 — Diary guide review lifecycle

## Why now

Diary → guide attach (SPEC-021) only covers enqueue / ready / publish / dismiss.
Authors need a full review loop: notes-driven regenerate, unpublish, abolish, delete.

## Outcome

1. Author submits **review notes** → recompose queued with notes (no HTML CMS edit).
2. **Unpublish** returns link to `ready_for_review` and hides from plaza.
3. **Dismiss** abolishes from review queue (unpublish first if needed).
4. **Delete** removes diary↔guide link; hard-deletes ListeningGuide when exclusive and not public.
5. UI exposes actions by derived `actions` flags; Studio visual path for guide preview unchanged.

## Non-goals

- WYSIWYG HTML editing
- Multi-round notes history table
- Ops batch approval
