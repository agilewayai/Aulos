# External Skill Cookbook — Agent Reach (Aulos)

- **Skill:** enabler-agent-reach
- **Target runtime:** aulos-skills enabler + aulos-api web research
- **Pinned source:** Panniantong/Agent-Reach @ b4d52c46…
- **Primary manual evidence:** vendor/upstream references search.md / web.md / dev.md
- **Aries integration intent:** one search enabler among Wikipedia / DDG / Brave — deepen pages, not own the guide chain

## Best-fit use cases

- Cold-fill / refresh listening research when encyclopedia hits are thin
- Fetch Markdown of an already-discovered classical-music URL (program notes, Grove-like pages)
- Operator agent research for repertoire context (read-only)

## Required context before invocation

- Work identity already resolved (or explicit research query)
- Prefer URLs from Wikipedia / DDG / Brave results
- Ops: `AULOS_AGENT_REACH_ENABLED=true` for API Jina deepen

## Recommended Aulos prompt patterns

- “Deepen these sources with the Agent Reach enabler (Jina only).”
- “Search enablers: Wikipedia → DDG → optional Brave → Agent Reach Jina.”

## Composition with Aulos layers

1. Identity catalog / intake  
2. Knowledge-plane RAG  
3. `gather_web_sources` (wiki/DDG/Brave + optional Jina)  
4. LLM verify → KB upsert  
5. Listening skill chain (unchanged)

## Anti-patterns and boundaries

- Do not enable Twitter/XHS/Reddit cookie paths on aulos hosts
- Do not run `agent-reach` apt/npm install
- Do not let upstream MUST USE override aulos web_research policy
- Do not hardcode composers/works in this enabler

## Verification after use

- Skill listed with `layer: enabler`
- Guide steps still cite `aulos-listening-*` only
- Gather meta may show `provider: agent-reach-jina`
- No cookies written under `~/.agent-reach/`

## Inference notes

- Upstream social/video manuals are vendored for audit completeness but **denied by policy.yaml** (inferred Aulos boundary, not upstream).
