---
schema_version: "0.1"
project_id: "aulos-workspace"
owner: "ubuntu"
doc_role: "harness-audit"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/review-audit/v1"
initialized_at: "2026-07-27T08:33:35Z"
effective_status: "active"
effective_since: "2026-07-27T08:33:35Z"
content_fingerprint: "sha256:a062e113f99dea7ef93c9a419af064040360623cb53cb1e81d349abe81faf076"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# AUDIT-009 - Workspace Architecture And Code Review

## Artifact Header

- Artifact ID: AUDIT-009
- Artifact type: harness-audit
- Status: complete
- Owner: ubuntu
- Canonical path: `aulos-skills/.aries_harness/runs/reviews/AUDIT-009-workspace-architecture-code-review-20260727T083335Z.md`
- Source of truth: current working tree at `2026-07-27T08:33:35Z`
- Upstream links: workspace `AGENTS.md`; `aulos-operating-defaults`; project MISSION/STATE/TASK_STACK/EVAL; active ARCH/REQ/SPEC files
- Downstream links: remediation list in this report
- Verification state: reviewed; API suite red; other local gates mostly green
- Last reviewed: `2026-07-27T08:33:35Z`
- Next review / refresh trigger: after F1-F4 remediation and full API suite green

## Runtime Links

- Run ID: RUN-009-WORKSPACE-REVIEW
- Task ID / Slice ID: TASK-009-ARCH-CODE-REVIEW
- Checkpoint ID: pending
- Approval Request ID: n/a
- Trace ID: n/a
- Eval Report ID: local verification summary below
- Audit Log ID: AUDIT-009

## Review Setup

- System / Harness: Aulos monorepo: `aulos-agent`, `aulos-api`, `aulos-web`, `aulos-mcp`, `aulos-skills`, `aulos-ops`, `aulos-knowledge`, `deploy`.
- Reviewer: Codex using `aries-harness` -> `aries-harness-review`.
- Generated at: `2026-07-27T08:33:35Z`.
- Git baseline: `0c8a847bde087752f8e0670b1a7cf9f12f522b2e`.
- Worktree state: dirty, 132 status entries. Existing user/operator changes were treated as review evidence and not reverted.
- Overall readiness: not ready for production signoff. The codebase has strong harness coverage and broad tests, but release-blocking security and verification findings remain open.
- Remaining human gate: operator acceptance after critical secret rotation and security-boundary remediation.

## Findings

| Finding ID | Severity | Issue | Impact | Smallest practical fix | Evidence | Owner | Due date | Remediation status | Promotion target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | critical | Host deploy ships fixed JWT secret and bootstrap superadmin credentials | Anyone with repo access can forge API JWTs for the deployed host if the default is live; bootstrap also reactivates/grants superadmin to the configured email on every boot | Remove secret defaults from tracked systemd units; require `.run/host.env`; fail startup/deploy on default values; rotate live JWT secret and bootstrap admin password | `deploy/systemd/user/aulos-api.service:23,26-28`; `deploy/start-host.sh:37-42`; `aulos-api/src/aulos_api/auth/tokens.py:10-24`; `aulos-api/src/aulos_api/services/bootstrap.py:30-63` | api/ops | 2026-07-27 | deferred (operator rotation) | policy + devops gate: no tracked production secret defaults |
| F2 | high | Generated guide HTML runs active scripts in a same-origin iframe and on public share pages without a documented CSP/sanitization boundary | A compromised LLM/source/dossier path can become same-origin script execution; with localStorage tokens this becomes account/session compromise risk | Isolate guide rendering on a separate origin or remove `allow-same-origin`; add strict CSP for public pages; sanitize/allowlist generated links and scripts; move player script to versioned static asset with tests | `aulos-web/src/App.tsx:56-67,919`; `aulos-api/src/aulos_api/routes/listening.py:45-319,712-725`; `aulos-skills/src/aulos_skills/guide_render.py:814-815`; `aulos-skills/src/aulos_skills/media_search.py:48-69,72-93` | web/api/skills | 2026-07-28 | closed | SPEC for guide HTML security contract + regression tests |
| F3 | high | Browser JWTs are stored in `localStorage` in both portals | Any XSS in the portal or guide iframe can exfiltrate bearer tokens; this amplifies F2 | Move auth to HttpOnly, Secure, SameSite cookies or another JS-inaccessible session design; add logout/CSRF tests appropriate to the chosen design | `aulos-web/src/api.ts:80-88,101-102`; `aulos-ops/src/api.ts:161-182`; F2 same-origin script boundary | web/ops/api | 2026-07-28 | closed | auth architecture ADR + security regression gate |
| F4 | high | API verification is currently red | Release confidence is below the Aulos harness gate; one stable failing test and one order-dependent DB worker error remain | Fix web-research freshness contract; make background worker lifecycle deterministic in tests and app shutdown; rerun full API suite | Full `aulos-api` suite: `87 passed, 1 failed, 1 error`; `tests/test_web_research.py::test_run_web_research_cold_fill_then_skip_when_fresh`; `tests/test_listening_guide.py::test_recompose_keeps_share_slug_and_updates_html` failed in full suite but passed isolated | api | 2026-07-27 | closed | EVAL/VR gate: full API pytest must be green |
| F5 | high | Knowledge-plane service exposes direct admin routes without service-layer auth; `admin_token` is configured but unused | The API proxy requires superadmin, but direct service exposure, local SSRF, host-network mistakes, or future binding changes can mutate sources, jobs, documents, quarantine/publish state, and artifact previews | Enforce bearer/shared-token auth in `aulos-knowledge` for `/v1/admin/*`; have `aulos-api` proxy attach it; narrow CORS; add tests for 401 direct admin access | `aulos-knowledge/src/aulos_knowledge/config.py:18,31`; `aulos-knowledge/src/aulos_knowledge/app.py:35-40`; `aulos-knowledge/src/aulos_knowledge/routes.py:96-149,169-294,348-409`; API proxy role gate at `aulos-api/src/aulos_api/routes/ops.py:760-783` | knowledge/api | 2026-07-28 | closed | knowledge-plane security SPEC + tests |
| F6 | medium | Workspace inventory and harness governance drift: `aulos-knowledge` is implemented but absent from root project tables and lacks a local `AGENTS.md` plus full harness baseline | Operators and future agents can miss a production service; harness closeout/history commands do not have a complete project contract | Add `aulos-knowledge` to root `README.md` and `AGENTS.md`; add local `AGENTS.md`, MISSION, EVAL, INDEX, RUNBOOK, RISKS, scripts/templates or explicitly mark it experimental | Root tables omit knowledge: `README.md:5-13`, `AGENTS.md:31-39`; existing code/docs under `aulos-knowledge/`; partial harness only has STATE/TASK_STACK/JOURNAL plus selected REQ/SPEC/ARCH | workspace/knowledge | 2026-07-29 | closed | harness well-organized gate |
| F7 | medium | Static host/proxy only sets cache headers; no security response-header baseline | Public portals and share pages miss cheap hardening such as `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, frame policy, and CSP where possible | Add header policy in `deploy/serve.py` and API public HTML responses; test expected headers for static, proxied, and `/g/{slug}` paths | `deploy/serve.py:64-66,132-152`; `aulos-api/src/aulos_api/routes/listening.py:719-725`; deploy tests currently cover cache/rate gate only | deploy/api | 2026-07-29 | closed | devops smoke + deploy header tests |
| F8 | medium | Long-lived background workers are started at API lifespan without clean stop/join/reset contracts | Test order can leak DB HA/listening/mail workers across fixture DBs; production shutdown can leave in-flight state implicit | Add lifespan shutdown handlers calling stop methods; make `stop_*` idempotent and joinable; expose test reset helpers for db_ha and mail_queue instead of private field mutation | `aulos-api/src/aulos_api/app.py:44-68`; `aulos-api/src/aulos_api/services/db_ha.py:325-341`; `aulos-api/src/aulos_api/services/mail_queue.py:211-228`; `aulos-api/src/aulos_api/services/listening_queue.py:270-289`; full-suite SQLite `table users already exists` error | api | 2026-07-28 | closed | runtime lifecycle ADR + test fixture gate |
| F9 | medium | Web-research freshness mixes source provenance with mutable DB document timestamps and takes the max timestamp | A later DB write can mask stale source provenance; tests can become clock/order dependent and production refresh can skip external re-verification incorrectly | Decide freshness from explicit source provenance first, not `updated_at`, or store separate `last_web_verified_at`; inject clock into `run_web_research` tests | `aulos-api/src/aulos_api/services/web_research.py:197-233,260-298`; isolated test failure in `tests/test_web_research.py:225-247` | api | 2026-07-28 | closed | SPEC-006/SPEC web-research freshness delta |
| F10 | medium | Large modules are crossing ownership boundaries | Harder review, weaker test targeting, and higher regression risk around routes, rendering, and operations UI | Split along existing seams: API route/service/repository, guide HTML hardening renderer, Ops tab modules, web studio/library/guide modules, skill chain orchestrator vs rendering | File sizes: `aulos-ops/src/App.tsx` 1676 lines, `aulos-web/src/App.tsx` 1062, `aulos-api/routes/ops.py` 971, `aulos-api/routes/listening.py` 800, `aulos-api/services/listening_guide.py` 1281, `aulos-skills/runtime.py` 1872, `aulos-skills/guide_render.py` 1158 | fleet | 2026-07-31 | closed (slice 1) | structural-refactor REQ/SPEC |
| F11 | medium | Secrets for external providers are stored as plaintext JSON in `SystemSetting` | DB dumps expose Mailgun, LLM, Brave, Discogs, and embedding keys/tokens | Document accepted Sprint-1 risk or add encryption-at-rest with key management and redacted audit logs | `aulos-api/src/aulos_api/services/mailgun.py:102-117`; `aulos-api/src/aulos_api/services/llm_providers.py:171-173`; `aulos-api/src/aulos_api/services/embeddings.py:117-132`; prior `AUDIT-008` already notes Discogs plaintext | api/ops | 2026-08-03 | closed (ADR-008) | secrets-at-rest ADR |
| F12 | low | Ops lint reports a React hook dependency warning | The session-scene restore effect can use stale `user` state after future edits; it keeps the lint gate warning instead of clean | Fix dependency or refactor effect so `npm run lint` is warning-free | `npm run lint` in `aulos-ops`: `src/App.tsx:163:28 react-hooks/exhaustive-deps` | ops | 2026-07-29 | closed | frontend lint gate |

## Measurable Acceptance

- F1: `deploy/start-host.sh` refuses to install services unless `AULOS_JWT_SECRET` and bootstrap admin password are non-default, non-empty, and sourced from ignored operator config; a live rotation memo records new secret deployment.
- F2/F3: a malicious guide/dossier fixture containing `<script>`, `javascript:` URLs, and localStorage reads cannot access portal tokens or parent DOM in Playwright/security tests.
- F4/F8/F9: `cd aulos-api && .venv/bin/pytest -q` passes in full-suite order three times in a row with no unhandled thread exceptions.
- F5: direct `aulos-knowledge` `/v1/admin/*` calls return 401 without service token; API superadmin proxy still succeeds.
- F6: `aulos-knowledge/AGENTS.md` and complete harness baseline exist; root `README.md` and `AGENTS.md` list the service; `history-status`/`well-organized` passes or records explicit exception.
- F7: deploy tests assert the security header baseline on static and proxied routes.
- F10: each refactor slice includes local tests and lowers the largest module sizes without changing behavior.
- F11: either ADR accepts plaintext DB secrets for Sprint-1 with backup controls, or settings are encrypted and tested.
- F12: `cd aulos-ops && npm run lint` exits with no warnings.

## Architecture Review

The intended architecture is sound for a hackathon monorepo:

- `aulos-web` and `aulos-ops` are Vite/React portals.
- `aulos-api` is the HTTP gateway, auth boundary, persistence boundary, and proxy to agent/knowledge services.
- `aulos-agent` is the LangGraph runtime and should own agent orchestration.
- `aulos-skills` owns domain skill packs, listening identity, rendering, and evaluation.
- `aulos-mcp` is a tool integration surface.
- `aulos-knowledge` is now a separate professional knowledge plane backed by Postgres/Redis/artifacts.
- `deploy` wires host systemd services, local static proxy, k3s ingress, rate gates, and asset versioning.

Strengths:

- Harness coverage is broad across the original subprojects: MISSION/STATE/TASK_STACK/EVAL/JOURNAL exist for agent, API, web, MCP, skills, and ops.
- Listening identity has moved toward Catalog/IdentityResolver instead of pure composer/work hardcoding.
- API delegates listening guide generation through `AgentProxy.run_listening`, and tests guard against reintroducing `SkillRuntime.iter_listening_chain` as the API orchestrator.
- DB HA closeout improved: API schema patches are applied in both ordinary init and HA engine configuration.
- There is meaningful offline verification: skills, agent, MCP, knowledge, frontends, and deploy tests mostly pass.

Primary architecture risks:

- Security boundaries are implicit where they should be explicit: deploy secrets, guide HTML execution, browser token storage, and direct knowledge-plane admin access.
- Runtime lifecycle is not yet a first-class contract. Worker start/stop state is global and leaks into test order.
- The new knowledge plane has outgrown the root workspace inventory and harness baseline.
- UI/API modules are dense enough that future product changes will be harder to review without smaller ownership seams.

## Code Review Notes

- `aulos-api/src/aulos_api/services/bootstrap.py` is too permissive for production: it re-verifies/reactivates the configured bootstrap superadmin and ensures the role even when the account already exists. That behavior is useful for local bootstrap but dangerous when paired with tracked production unit defaults.
- `aulos-api/src/aulos_api/routes/listening.py` contains routing plus public HTML rewriting plus JS/CSS string patches. Move serve-time patching into a renderer/security module so public page behavior has focused tests and a CSP contract.
- `aulos-web/src/App.tsx` and `aulos-ops/src/App.tsx` are doing state orchestration, routing, forms, menus, API result shaping, and session-scene capture in one file. The current builds pass, but this is already beyond comfortable review size.
- `aulos-knowledge/src/aulos_knowledge/routes.py` is simple and testable, but admin and public APIs share one router without auth dependencies. Add dependencies before adding more mutation endpoints.
- `aulos-api/src/aulos_api/services/web_research.py` has the right policy concept, but `_kb_freshness_ts` should not let a DB row update time override explicit source verification provenance when deciding external refresh.
- The codebase generally avoids tracked cache/build artifacts. `git ls-files` found no tracked `__pycache__`, `.pyc`, `dist`, `.run`, `.env`, or `data` paths.

## Verification Evidence

Commands run:

| Area | Command | Result |
| --- | --- | --- |
| API | `cd aulos-api && .venv/bin/pytest -q` | failed: `87 passed, 1 failed, 1 error, 4 warnings` in 205.64s |
| API isolated recompose | `cd aulos-api && .venv/bin/pytest -q tests/test_listening_guide.py::test_recompose_keeps_share_slug_and_updates_html` | passed, proving the full-suite error is order/lifecycle dependent |
| API isolated web research | `cd aulos-api && .venv/bin/pytest -q tests/test_web_research.py::test_run_web_research_cold_fill_then_skip_when_fresh` | failed, stable web-research contract bug |
| Skills | `cd aulos-skills && .venv/bin/pytest -q` | `48 passed` |
| Agent | `cd aulos-agent && .venv/bin/pytest -q` | `10 passed` |
| MCP | `cd aulos-mcp && .venv/bin/pytest -q` | `4 passed` |
| Knowledge | `cd aulos-knowledge && .venv/bin/pytest -q` | `12 passed, 2 warnings` |
| Web build | `cd aulos-web && npm run build` | passed |
| Web lint | `cd aulos-web && npm run lint` | passed |
| Ops build | `cd aulos-ops && npm run build` | passed |
| Ops lint | `cd aulos-ops && npm run lint` | passed with one warning |
| Deploy tests | `aulos-api/.venv/bin/python -m pytest -q deploy/test_rate_gate.py deploy/test_serve_cache.py` | `4 passed` |

Warnings to track:

- Knowledge pytest: unknown `asyncio_mode` config option and Starlette/httpx deprecation.
- API pytest: Starlette/httpx deprecation, passlib `crypt` deprecation, FastEmbed pooling warning, unhandled DB HA thread exception.

## Coverage Against Aries Review Lenses

- Target clarity: good. Product/project roles are explicit for the original six subprojects.
- Scope discipline: partial. `aulos-knowledge` is now in deploy and code but not the root project contract.
- Runtime alignment: partial. Runtime artifacts exist, but no root workspace harness and worker lifecycle lacks clean shutdown.
- Routing boundaries: mostly good. API owns auth/proxy/persistence; skills own listening domain. The guide HTML serve-time patching blurs API vs renderer.
- Context hygiene: good enough for a hackathon tree, but large modules and dirty worktree increase review load.
- Verification: partial. Most gates pass; API full suite is red.
- Observability: adequate in API routes and queues; better than average for a hackathon repo, but worker lifecycle and public security headers need stronger gates.
- Recovery: partial. DB HA/failover exists, but worker shutdown and test isolation are not robust.
- Human approval boundaries: good in docs for live/deploy/secrets, weak in tracked deploy defaults.
- Reusability: good harness templates and repeatable local commands; needs knowledge-plane inclusion.
- Remediation closure: open, tracked by this audit.
- Signoff closeout readiness: not ready until F1-F4 are closed.

## Signoff Recommendation

- Ready for production signoff: no.
- Ready for continued local/hackathon iteration: yes, with F1 treated as immediate production-blocking remediation.
- Required before public confidence claim: close F1-F4, add F5 service auth, rerun full verification, and refresh harness history.
- Recommended next slice: security-first remediation, then API verification stabilization, then knowledge-plane harness alignment.
