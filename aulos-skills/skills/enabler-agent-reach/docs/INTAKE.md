# External Skill Intake — Agent Reach

- **Requested skill:** Agent Reach (multi-platform internet search/read router)
- **Target runtime:** Aulos agent skill library (`aulos-skills`, Codex-style `SKILL.md` + `skill.yaml`)
- **Discovery source:** GitHub search for agent-reach skills; hub mirrors (openclaw / Skillselion) as discovery only
- **Selected install source:** `https://github.com/Panniantong/Agent-Reach` @ `b4d52c46c9113cb0f653d6df4cf71ebadf4930ac` → `agent_reach/skill/`
- **Primary manual source:** `vendor/upstream/SKILL.md` + `references/{search,web,dev}.md`
- **Trust level:** Conditional — owner repo + MIT + recent hardening; social/cookie/install surfaces denied
- **Compatibility note:** Upstream is OpenClaw/agent CLI router with `MUST USE` triggers. Aulos wraps it as `layer: enabler` without listening-chain triggers; softens MUST USE; composes with `web_search` / `web_research`.
- **Aries cookbook path:** `docs/COOKBOOK.md`
- **Install command:** vendored under `aulos-skills/skills/enabler-agent-reach/` (this pack); API deepen via `AULOS_AGENT_REACH_ENABLED`
- **Update command:** re-fetch pinned owner tree, bump `PIN.json`, re-run `docs/SECURITY_AUDIT.md` checklist, refresh vendor/
- **Removal command:** delete `aulos-skills/skills/enabler-agent-reach/`; set `AULOS_AGENT_REACH_ENABLED=false`; remove related web_search hooks if desired
- **Follow-up verification:** `aulos-skills` discovers `enabler-agent-reach`; web gather includes `agent-reach-jina` when enabled; listening chain unchanged (no new triggers)
