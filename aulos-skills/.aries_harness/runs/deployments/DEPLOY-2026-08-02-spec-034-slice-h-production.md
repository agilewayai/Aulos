---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "deployment-evidence"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-02T10:02:45Z"
effective_status: "active"
effective_since: "2026-08-02T10:02:45Z"
content_fingerprint: "sha256:808dd7e58c3a42f5a1c188183a30ee64c7712ae0b49c49174937133b2de89aec"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# DEPLOY - SPEC-034 Slice H production

- Environment: production host, systemd user units + k3s ingress
- Public URLs: `https://aulos.purezen.ai`, `https://aulos-ops.purezen.ai`
- Candidate branch/ref: `main` at `9606691`
- Candidate cleanliness: dirty working tree; this was not a clean committed
  release-candidate deploy
- Approval: operator explicitly requested production deploy in the current turn
- Deploy command: `bash deploy/aulos-ctl.sh deploy` completed successfully
- Deploy time evidence: `aulos-api`, `aulos-web`, and `aulos-ops` restarted at
  `2026-08-02 18:01:53 CST`; `aulos-knowledge` restarted at
  `2026-08-02 18:01:50 CST`

## Release Unit

SPEC-034 Slice H promotes the guide #60 root-cause fix:

- PostgreSQL RCA showed the apparent "step 3" delay was not RAG. The trace
  moved from `discogs.structure` to `rag` in about 0.004s, then spent about
  711.6s in `program.deepen_loop` and about 174.6s in `llm_enrich`.
- Multi-work `g.program` now defaults to fast/budgeted execution: raw web floor,
  no per-work Jina, no verify LLM, no per-work LLM dossier, and no album LLM
  unless the operator opts into full mode.
- Sheet fan-in parses JSON notes before prose synthesis, suppresses raw
  JSON/caveat payloads, and provides identity floors for raw-web-only sheets.
- Instrument evidence recognizes German/European piano, flute, and cello terms
  (`Klavier`, `Flöte`, `Violoncello`, etc.) without false solo-concerto drift.
- Product gates remain fail-closed: guide #60 still fails publication on
  `ambient_ok=false` until a work-matched media/ambient candidate is available.

Built frontend artifacts observed after deploy:

- Web `version.json`: `20260802100144-9606691`
- Ops `version.json`: `20260802100212-9606691`

## PostgreSQL Evidence

Production PostgreSQL query, not SQLite:

- Latest matching guide: `listening_guides.id=60`
- Status: `failed`
- Composer/title:
  `Johann Nepomuk Hummel / Carl Maria Von Weber / Joseph Haydn` /
  `Trios Für Klavier, Flöte Und Violoncello`
- Error detail: `eval_pass=false; ambient_ok=false`
- HTML length: `113101`
- Created/updated:
  `2026-08-02 07:33:18.252722+00:00` /
  `2026-08-02 07:48:26.847023+00:00`
- Structure trace: `multi_work_program`, `structure_ready=true`,
  `program_count=3`
- RAG trace: `hit_count=16`
- Program deepen trace: `works=3`, `with_evidence=3`

## Verification

Preflight:

- `bash deploy/aulos-ctl.sh doctor` -> ready for deploy
- Checks included host env secrets, kubectl, loginctl linger, ports `5090`,
  `5091`, `5092`, `5095`, Postgres `5433`, and Redis `6379`

Production deploy and smoke:

- `bash deploy/aulos-ctl.sh deploy` -> completed successfully
- Deploy script built `aulos-web` and `aulos-ops`, installed systemd user units,
  applied k3s ingress manifests, restarted host services, and ran local/public
  smoke successfully
- `bash deploy/aulos-ctl.sh smoke` -> all smoke checks passed
- Local API `/health`: `status=ok`, `db_ha.active_role=primary`,
  `primary_ok=true`, `failover_ok=true`
- Local web `:5091`: OK
- Local ops `:5092`: OK
- Local knowledge `/health`: `status=ok`
- Public smoke for web and ops domains returned API `/health` OK

Production status:

- `bash deploy/aulos-ctl.sh status` -> all four services active/running:
  `aulos-api`, `aulos-web`, `aulos-ops`, `aulos-knowledge`
- k3s ingress present for `aulos.purezen.ai` and `aulos-ops.purezen.ai`

Focused checks run before deploy:

- Skills focused tests: `20 passed`
- Skills wider listening runtime slice: `44 passed`
- API focused research/deepen/listening suites: green in split runs
- Ops build: `npm run build` passed

## Rollback

- Rollback owner: human host operator
- Rollback command: checkout a known-good SHA and run
  `bash deploy/aulos-ctl.sh deploy`
- No rollback was triggered; status and smoke stayed green

## Residuals

- Guide #60 remains failed by design because `ambient_ok=false` is a product
  gate; this slice fixes analysis drift/thinness/latency defaults, not the
  missing work-matched media candidate.
- No live recompose of guide #60 was run after deploy to avoid publishing a
  guide that still lacks ambient media.
- Full API combined pytest previously had green test assertions but exited
  `134` after summary, likely native cleanup/threading; split suites exited 0.
