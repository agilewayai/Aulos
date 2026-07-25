---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:10:00Z"
effective_status: "active"
effective_since: "2026-07-25T17:10:00Z"
content_fingerprint: "sha256:eaeca628220c9e1c56450c4f99fe9a965edd76a84da2f4fac79a467213e128c3"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-002 — Agent-orchestrated listening (导赏)

## Design Drivers

- Product power core is **Agent + Skill Harness + tools**, not API Python orchestration.
- Listening guides must be produced by the agent calling skill tools step-by-step.
- Offline/fake must remain green without live LLM keys.

## Target shape

```text
aulos-web → aulos-api (auth, RAG inject, persist, SSE)
         → aulos-agent (ReAct / playbook fake)
         → tools.run_listening_skill(trigger)
         → aulos-skills SkillRuntime.run_trigger
         → skills/*/skill.yaml + SKILL.md
```

## Boundaries

- **API must not** call `SkillRuntime.iter_listening_chain` / stepwise `run_trigger` as product orchestration.
- **Agent** owns tool selection and step order (playbook from `aulos-listening` skill).
- **Skills** own per-trigger domain behavior; tools are thin adapters.

## Integration

- Default local path: API imports `aulos_agent.listening.service` in-process (fake_agent or missing agent URL).
- Optional remote: `POST {agent_base_url}/v1/listening/run` when agent is configured live.

## Related

- ADR-003, SPEC-002 (agent)
- aulos-api SPEC-003 delta
- aulos-skills ADR-002 consequences
