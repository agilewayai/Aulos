# Listening Guide Revise (SPEC-022Δ)

Proofread and repair the Salon Codex page **against the expert review report**,
then re-compose. Dual scorecards must show substantive hard-flaw delta.

## Procedure

1. Keep `generation_rounds.draft_v1` intact (already re-scored with review penalties).
2. Deterministic repair (`apply_review_repairs`): identity hygiene, scrub foreign
   chambers, clear bad portrait, inject listening map / anatomy if missing, pin
   `REVIEW REPAIR` + `critique_corrections`.
3. Optional LLM proofread (`llm_revise_complete`): rewrite thesis / points / map
   from the hard-flaw report (JSON patches only).
4. Re-run compose render under repaired context.
5. Store as `draft_v2` with hard-flaw-aware scorecard; primary `guide_html` = v2.

## Quality bar

- Address every high-severity review finding when possible
- `comparison.delta_hard_flaws` should improve when repairs land
- Score v2 uses remaining hard-flaw scan — not a copy of v1's card
