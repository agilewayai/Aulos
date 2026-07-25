---
schema_version: "0.1"
project_id: "aulos-api"
owner: "arthur"
doc_role: "story-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:47:11Z"
effective_status: "active"
effective_since: "2026-07-25T11:47:11Z"
content_fingerprint: "sha256:3cf5ee02aacd3a2f73293c535e411ac4aefc591d19c033932819ab375a7779f7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# STORY-PACK-002 — Auth MVP

### STORY-002 — Users/roles + register/verify/login API
- Done when: pytest green for auth flows + role guards

### STORY-003 — Mailgun provider + ops config API
- Done when: superadmin can GET/PUT Mailgun settings; fake provider works without network

### STORY-004 — aulos-web register/login/verify UI
- Done when: forms usable, labels accessible, loading/error feedback

### STORY-005 — aulos-ops superadmin gate + Mailgun settings UI
- Done when: non-superadmin blocked; superadmin can save Mailgun config
