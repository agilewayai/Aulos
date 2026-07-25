# Aulos Skills

Main harness work package for the Aulos initiative — skill registry, playbooks, and operator CLI. Governed by [aries-harness](.aries_harness/).

## Architecture

```text
aulos-skills CLI / SkillRuntime
   └─ registry.discover_skills(skills/*)
         ├─ operator: aulos-core, aulos-operating-defaults, …
         └─ domain-runtime (导赏):
              aulos-listening → intake → corpus → width → depth → compose → eval
```

| Path | Role |
| --- | --- |
| `skills/` | Skill packs (`skill.yaml` + `SKILL.md`) |
| `skills/aulos-listening*` | Classical listening-guide domain skills |
| `src/aulos_skills/registry.py` | Manifest discovery |
| `src/aulos_skills/cli.py` | `aulos-skills list\|show` |

Design source of truth:

- Operator harness: `ARCH-001`
- Agent × skills 导赏: `ARCH-002` / `ADR-002` / `REQ-002` / `SPEC-002`

## Quick start

```bash
cd aulos-skills
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

aulos-skills list
aulos-skills show aulos-core
```

## Verify

```bash
pytest -q
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder: `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`
