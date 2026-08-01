# Listening External Review (SPEC-022Δ)

After the first compose draft, an **External Review Agent** reviews as a senior
**音乐导赏专家 + 音乐分析专家**, looking for hard flaws (硬伤) — not hunting web sources.

## Procedure

1. Snapshot draft_v1 HTML if not already stored in `generation_rounds`.
2. Identity hygiene (portrait, foreign family, H1 drift) — still hard flaws.
3. Expert craft / analysis scan: foreign chambers in body, celebrity H1 pollution,
   form≠title, missing listening map / anatomy, rival-composer dominance.
4. Optional LLM expert pass (`llm_external_review_complete`) — same perspective;
   must not emit source-coverage findings.
5. Emit `external_review_report` (`aulos.external_review/v1`, `perspective=
   music_guide_and_analysis_expert`) and `critique_corrections` for revise.

## Outputs

- `external_review_report` (findings + required_corrections)
- `critique_corrections` for `listening.revise`
- Updated `generation_rounds.review_report`
