---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "deployment-evidence"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-02T07:24:00Z"
effective_status: "active"
effective_since: "2026-08-02T07:24:00Z"
content_fingerprint: "sha256:ac05be37e83fbec529be0a51dee7ed4925f65dd8a5da4f722e710f20bfbaa483"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# DEPLOY — SPEC-034 Slice G production

- Environment: production host, systemd user units + k3s ingress
- Public URLs: `https://aulos.purezen.ai`, `https://aulos-ops.purezen.ai`
- Candidate branch/ref: `main` at `5476efb`
- Candidate cleanliness: dirty working tree; this was not a clean committed
  release-candidate deploy
- Approval: operator explicitly requested production deploy in the current turn
- Deploy command: `bash deploy/aulos-ctl.sh deploy` completed successfully
- Deploy time evidence: services restarted at `2026-08-02 15:18:36/38 CST`

## Release Unit

SPEC-034 Slice G promotes the multi-work guide sheet contract:

- `guide_sheets[]` with one work sheet per ready program work and one synthesis
  sheet
- `program_parallel_plan` with deterministic fan-out work units and
  `fan_in="synthesis_sheet"`
- accessible sheet tabs in generated guide HTML

Built frontend artifacts observed after deploy:

- Web: `aulos-web/dist/assets/index-C4PhANvp.js`
- Ops: `aulos-ops/dist/assets/index-6KD2tYCV.js`
- Web `version.json`: `20260802071831-5476efb`
- Ops `version.json`: `20260802071835-5476efb`

## Verification

Preflight:

- `bash deploy/aulos-ctl.sh doctor` -> ready for deploy
- Checks included host env secrets, kubectl, loginctl linger, ports `5090`,
  `5091`, `5092`, `5095`, Postgres `5433`, and Redis `6379`

Deploy-layer tests:

- `bash deploy/aulos-ctl.sh test` -> `5 passed in 0.02s`

Production status:

- `bash deploy/aulos-ctl.sh status` -> all four services active/running:
  `aulos-api`, `aulos-web`, `aulos-ops`, `aulos-knowledge`
- k3s ingress present for `aulos.purezen.ai` and `aulos-ops.purezen.ai`

Production smoke:

- `bash deploy/aulos-ctl.sh smoke` -> all smoke checks passed
- Local API `/health`: `status=ok`, `db_ha.active_role=primary`,
  `primary_ok=true`, `failover_ok=true`
- Local web `:5091`: OK
- Local ops `:5092`: OK
- Local knowledge `/health`: `status=ok`
- Public smoke for web and ops domains returned API `/health` OK

Runtime logs:

- API restarted cleanly; db HA, mail, listening, and ops task workers started
  and reported Redis OK
- API served `/health`, `/v1/auth/me`, guide list, plaza, and ops endpoints
  with HTTP 200 after restart
- Web and Ops static hosts served `/`, `/health`, `version.json`, and built JS
  assets with HTTP 200 after restart
- Knowledge restarted cleanly and served `/health` with HTTP 200

## Rollback

- Rollback owner: human host operator
- Rollback command: checkout a known-good SHA and run
  `bash deploy/aulos-ctl.sh deploy`
- No rollback was triggered; status and smoke stayed green

## Residuals

- No live secret rotation was performed in this deployment.
- Live guide `#59` was not recomposed after deploy; the next product check is to
  regenerate it and verify sheet tabs plus per-work sheets in persisted output.
- No browser/Playwright visual smoke was run; this closeout covers scripted
  health/static/API smoke and logs.
- Actual concurrent worker execution was not shipped in this slice; Slice G
  emits the safe fan-out/fan-in plan for a later gateway/agent orchestration
  slice.
