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
content_fingerprint: "sha256:2ee2947b00457ab69c8ecf3c6e0ede26314bdea79375054b840e51cac3002e5e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

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

- Optional: regenerate multi-work Discogs probe guides after deploy to confirm IntentLock freeze + multi_work status in production.
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
- Skills: compose/eval 0.3.0, synthesize 0.2.0, corpus 0.3.0, operating-defaults 0.3.3
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-ops, aulos-knowledge
- Timezone: store UTC / display OS local (operating-defaults 0.3.3; SPEC-007 on api)

## Open risks

- AUDIT-009 residual deferred: F1 live credential rotation (operator); further F10 splits for largest skill/API modules.
- Cold Discogs works without Catalog `work_id` still lean on LLM/KB; decontam markers are catalog-derived aliens — sparse catalog ⇒ weaker alien set
- Cross-service contract drift (web sandbox / API media vs skills SPEC-006)
- Formal RUN-* template not yet mandatory on every slice
