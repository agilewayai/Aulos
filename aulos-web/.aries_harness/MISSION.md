---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:2345349c82adc00d80ecb81e1f9e092453f77f7ce11e2727535024cccec23113"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

## Outcome

- Deliver an operator web GUI (`aulos-web`) that chats with Aulos through the API gateway under aries-harness governance.

## Scope boundary

- In scope: Vite/React TypeScript console, gateway client, offline build verification, harness artifact ladder
- Out of scope: auth/SSO, production hosting, custom design system package, mobile native apps

## Success test

- npm build succeeds; chat UI posts to `/v1/chat`; ARCH/SPEC/STORY linked; harness mission/state updated

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
