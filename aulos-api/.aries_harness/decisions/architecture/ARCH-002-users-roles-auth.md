---
schema_version: "0.1"
project_id: "aulos-api"
owner: "arthur"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:47:11Z"
effective_status: "active"
effective_since: "2026-07-25T11:47:11Z"
content_fingerprint: "sha256:e30a2cdfdceb380de2e354d39fc13716162b8d893b02180de1f06db1121888ac"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-002 — Users/roles auth architecture

## Shape
```text
aulos-web (register/login/verify)
   │
   ▼
aulos-api ── auth routes ── User/Role (SQLite)
   │              │
   │              └── MailgunClient (live | fake)
   │
aulos-ops (superadmin) ── /v1/ops/mailgun settings
```

## Modules
- `db.models` — User, Role, EmailToken, SystemSetting
- `auth` — password hash, JWT, FastAPI deps (`get_current_user`, `require_roles`)
- `services.mailgun` — send verification email
- `services.bootstrap` — ensure roles + optional superadmin

## Security
- bcrypt passwords; JWT HS256 with `AULOS_JWT_SECRET`
- verification tokens hashed at rest; single-use; TTL
- Mailgun API key stored in SystemSetting (not committed)
