---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T16:20:00Z"
content_fingerprint: "sha256:77b0a3fb3d158ba8bbd00308242e74a067e10d36477d77fff66e043932c43fe0"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- SPEC-034 Slice H deployed: production guide #60 RCA confirmed the perceived
  "step 3" latency was actually `g.program` (~711.6s) plus album `g.llm`
  (~174.6s) on PostgreSQL trace; default multi-work deepen is now
  fast/budgeted, JSON notes are parsed before sheet fan-in, raw-web sheets get
  identity floors, and German trio instrument terms no longer false-flag solo
  drift. Production deploy and scripted smoke passed on 2026-08-02T10:02Z;
  guide #60 remains failed by design on `ambient_ok=false`.
- SPEC-034 Slice G deployed to production: multi-work guides now emit work
  sheets + synthesis sheet and render accessible sheet tabs;
  `program_parallel_plan` exposes fan-out/fan-in metadata for future
  worker-safe orchestration.
- SPEC-034 Slice F / META-001 v10 code deployed: program fold-back owns final
  subject; failed eval/process gates fail closed (guide #59 recompose pending)
- SPEC-034Δ / REQ-024 Discogs release-structure + program deepen + META-001 **v9** (canonical query + LLM-optional)
- SPEC-033 / REQ-023 Instrument-faithful thicken + multi-work Discogs (anti-case) shipped
- SPEC-032 / REQ-022 Identity freeze + Catalog/facet hardening (anti-case) shipped
- SPEC-031 / REQ-021 Dimensional thicken + promote-to-production (anti-case) shipped
- SPEC-030 / REQ-020 Promote staging + ops surface shipped
- SPEC-029 / REQ-019 Unknown-Case Thicken Loop v1 shipped
- SPEC-028 / REQ-018 Catalog craft coverage + fleet dossier ensure shipped
- SPEC-027 / REQ-017 genre family coverage + Catalog family lock shipped
- SPEC-026 / REQ-016 systemic cold-path thicken (catalog floor + auto dossier + asset_depth) shipped
- SPEC-025 / REQ-015 knowledge thicken + ProductScorecard dual-track shipped
- SPEC-024 / REQ-014 craft raise (Work Resolver + chamber contracts + cold thicken) shipped
- SPEC-023 / REQ-013 product-prose hygiene (packaging / process locks / bilingual / review honesty) shipped
- SPEC-022Δ targeted revise + revision_history (shipped)
- SPEC-006Δ ambient: no library rotation; embed|stream OPS fallback (shipped)
- SPEC-022 external review round: compose → networked external_review → revise → dual draft eval (shipped + deployed)
- SPEC-009Δ / SPEC-019 self-heal: guide #48 identity hygiene (portrait / foreign family / H1)
- SPEC-019 process scorecard (NodeScorecard + ProcessScorecard) shipped for listening atelier.
- SPEC-018 adversarial process review (hybrid Intent Critic) shipped for listening atelier.
- AUDIT-009 F2/F10/F11 closed: guide HTML security contract + sanitizer, module splits, plaintext-secrets ADR.
- F1 deferred (operator live secret rotation only).
- F3 session cookies already shipped (SPEC-014).
- SPEC-009 node decontam + family evidence gate (Brahms Op.77 / guide #44)
- Process remediation: harness mandatory + facility under `.aries_harness/` + self-evolution closeout

## Active run

- Closed + deployed: SPEC-034 Slice H guide #60 program-deepen latency /
  subject-thickness RCA + code (2026-08-02); focused tests, production deploy,
  smoke, status, and PostgreSQL evidence green. `ambient_ok=false` remains a
  fail-closed residual.
- Closed + deployed: SPEC-034 Slice G multi-work guide sheets + synthesis
  fan-in (2026-08-02); production status/smoke green.
- Closed + deployed: SPEC-034 Slice F guide #59 fold-back scalar ownership +
  API failed-gate persistence (2026-08-02); live guide #59 recompose pending.
- Closed: META-001 v9 canonical program query + LLM-optional web floor (2026-08-01)
- Closed: SPEC-034Δ iterative program deepen loop + META-001 v8 (2026-08-01)
- Closed: STORY-PACK-002 Slice B/C — runtime hard-gate + program expand (2026-08-01)
- Closed: REQ-024 / SPEC-034 Slice A structure domain + emit + META-001 v7 (2026-08-01)
- Next: Slice E live recompose after deploy (confirm atelier `g.program` + `release-program-loop`)
- Closed: REQ-023 / SPEC-033 Instrument-faithful thicken + multi-work Discogs (2026-08-01)
- Closed: REQ-022 / SPEC-032 Identity freeze + Catalog/facet hardening (2026-08-01)
- Closed: REQ-021 / SPEC-031 Dimensional promote anti-case (2026-08-01)
- Closed: REQ-020 / SPEC-030 Promote staging + ops surface (2026-08-01)
- Closed: REQ-019 / SPEC-029 Unknown-Case Thicken Loop v1 (2026-08-01)
- Closed: REQ-018 / SPEC-028 Catalog craft + fleet dossier (2026-08-01)
- Closed: REQ-017 / SPEC-027 genre family coverage (2026-08-01)
- Closed: REQ-016 / SPEC-026 systemic cold-path thicken (2026-08-01)
- Closed: REQ-015 / SPEC-025 knowledge thicken + ProductScorecard + guide #50 (2026-08-01)
- Closed: REQ-014 / SPEC-024 craft raise + guide #50 eval 10 (2026-08-01)
- Closed: REQ-013 / SPEC-023 product-prose hygiene + guide #50 regen (2026-08-01)
- Closed: SPEC-022Δ targeted chamber revise + revision_history (2026-08-01)
- Closed: REQ-005 / SPEC-006Δ ambient library off + YT/Bili embed|stream (2026-08-01)
- Closed: REQ-012 / SPEC-022 external review round (2026-08-01) — deployed; guide #48 regenerated with generation_rounds
- Closed: guide #48 identity hygiene + scorecard critique loop (2026-08-01)
- Closed: REQ-009 / SPEC-019 process scorecard (2026-08-01)
- Closed: REQ-008 / SPEC-018 / ADR-005 adversarial review (2026-08-01)
- Closed: AUDIT-009 F2/F10/F11 continuation (2026-07-27)
- Closed: AUDIT-009 workspace architecture/code review (2026-07-27)
- Closed: REQ-007 / SPEC-009 decontam slice (2026-07-26)

## Next action

- Do not loosen `ambient_ok=false`; recompose guide #60 only after a
  work-matched media/ambient candidate is available or a separate media slice
  resolves the ambient gate.
- Optional: recompose guide #59 and multi-work / non-piano concerto Discogs
  probes to confirm sheet-mode guide rendering live.
- Optional: expand dimension **voice tables** and form_lock aliens from live Discogs facet histograms — still dimensional, never per-work craft.
- Optional: knowledge-plane auto-thicken after promote-production (composer stub → dossier job).
- Optional operator: rotate live secrets in `.run/host.env` when ready to redeploy (F1 deferred).
- Later: fleet-wide adversarial review + gateway-stage scorecards (phase 2).
- Later: deeper F10 splits (`listening_guide.py` / `runtime.py`) when product work touches those files.

## Blockers

- None for local/hackathon iteration. Production signoff still optional on F1 credential rotation.

## Hot facts

- Project root: `aulos-skills/`
- Role: main harness skills
- Live gates: bilingual + ambient required; media `inline`; foreign-chamber scrub; **per-node decontam rework**
- Family match: composer-scoped packs need instrument/form evidence (not composer alone)
- Facility: `.aries_harness/{scripts,templates}` (not package-root)
- Canonical harness library: `git@github.com:agilewayai/aries-harness-skills.git` (`0.10.0-preview.10`)
- Skills: compose 0.3.1, eval 0.3.1, synthesize 0.2.2, corpus 0.3.0, operating-defaults 0.4.2
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-ops, aulos-knowledge
- Timezone: store UTC / display OS local (operating-defaults 0.3.3; SPEC-007 on api)

## Open risks

- AUDIT-009 residual deferred: F1 live credential rotation (operator); further F10 splits for largest skill/API modules.
- Cold Discogs works without Catalog `work_id` still lean on LLM/KB; decontam markers are catalog-derived aliens — sparse catalog ⇒ weaker alien set
- Cross-service contract drift (web sandbox / API media vs skills SPEC-006)
- Formal RUN-* template not yet mandatory on every slice
