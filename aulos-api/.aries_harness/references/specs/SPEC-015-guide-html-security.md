---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T09:20:00Z"
effective_status: "active"
effective_since: "2026-07-27T09:20:00Z"
content_fingerprint: "sha256:911a23bf60341a67ca334a7840807d0d5da189812758123fb53b5e6780a3b7c3"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-015 — Guide HTML security contract (AUDIT-009 F2)

## Problem

Generated listening-guide HTML may contain LLM/dossier-sourced markup. Running it as same-origin script in the portal iframe, or on public share pages without CSP/sanitization, can become XSS and session theft (amplified when tokens were in `localStorage`).

## Contract

1. **Studio iframe** (`aulos-web`): `sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"` — **no** `allow-same-origin`. Scripts run in an opaque origin and cannot read portal cookies/DOM/`localStorage`.
2. **Public share** (`GET /v1/public/guides/{slug}`):
   - Apply `prepare_public_guide_html`: sanitize dangerous URL schemes + strip inline `on*` handlers, then serve-time chrome harden.
   - Response headers include CSP (`PUBLIC_GUIDE_CSP`) and baseline security headers.
3. **Sanitizer** (`aulos_api.services.guide_html_security`):
   - Neutralize `javascript:`, `vbscript:`, and `data:text/html` in `href`/`src`/`action`/`formaction`.
   - Strip HTML event-handler attributes (`onclick`, `onerror`, …).
   - Preserve intentional ambient/share scripts injected after sanitize.

## Non-goals

- Full HTML allowlist sanitizer (bleach/DOMPurify) — deferred
- Separate static origin for guides — deferred
- Playwright browser automation in CI — optional stretch; unit/API tests are the Sprint-1 gate

## Acceptance

- Unit tests cover sanitize fixtures with `<script>`, `javascript:` URLs, and `onerror`.
- Public guide responses assert CSP + security headers.
- Web selftest asserts iframe sandbox omits `allow-same-origin`.
- Portal auth uses HttpOnly cookies (SPEC-014), so even if a future sandbox regression occurs, tokens are not JS-readable.
