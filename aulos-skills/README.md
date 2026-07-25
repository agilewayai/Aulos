# Aulos Skills

Main harness work package for the Aulos initiative — skill registry, playbooks, and operator CLI. Governed by [aries-harness](.aries_harness/).

## Architecture

```text
aulos-skills CLI
   └─ registry.discover_skills(skills/*)
         ├─ aulos-core
         ├─ aulos-service-bootstrap
         └─ aulos-ops-observability
```

| Path | Role |
| --- | --- |
| `skills/` | Skill packs (`skill.yaml` + `SKILL.md`) |
| `src/aulos_skills/registry.py` | Manifest discovery |
| `src/aulos_skills/cli.py` | `aulos-skills list\|show` |

Design source of truth: `.aries_harness/decisions/architecture/ARCH-001-skills-harness-architecture.md`

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
bash scripts/aries-harness/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder: `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`
