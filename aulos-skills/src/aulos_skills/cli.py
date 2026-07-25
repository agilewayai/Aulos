from __future__ import annotations

import argparse
import json
from pathlib import Path

from aulos_skills.config import get_settings
from aulos_skills.registry import discover_skills


def _package_root() -> Path:
    # aulos-skills/ when running from editable install in workspace
    return Path(__file__).resolve().parents[2]


def cmd_list(as_json: bool = False) -> int:
    settings = get_settings()
    roots = settings.resolved_roots(_package_root())
    skills = discover_skills(roots)
    if as_json:
        payload = [
            {
                "id": s.skill_id,
                "name": s.name,
                "layer": s.layer,
                "version": s.version,
                "summary": s.summary,
                "path": str(s.path),
            }
            for s in skills
        ]
        print(json.dumps(payload, indent=2))
        return 0

    if not skills:
        print("No skills found.")
        return 0
    for skill in skills:
        print(f"{skill.skill_id:28} [{skill.layer}]  {skill.summary}")
    return 0


def cmd_show(skill_id: str) -> int:
    settings = get_settings()
    roots = settings.resolved_roots(_package_root())
    skills = {s.skill_id: s for s in discover_skills(roots)}
    skill = skills.get(skill_id)
    if skill is None:
        print(f"Skill not found: {skill_id}")
        return 1
    readme = skill.path / "SKILL.md"
    print(f"# {skill.name} ({skill.skill_id})")
    print(f"layer: {skill.layer}")
    print(f"version: {skill.version}")
    print(f"path: {skill.path}")
    print()
    if readme.is_file():
        print(readme.read_text(encoding="utf-8"))
    else:
        print(skill.summary)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Aulos harness skills CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List registered skills")
    list_parser.add_argument("--json", action="store_true")

    show_parser = sub.add_parser("show", help="Show a skill manifest + SKILL.md")
    show_parser.add_argument("skill_id")

    args = parser.parse_args()
    if args.command == "list":
        raise SystemExit(cmd_list(as_json=args.json))
    if args.command == "show":
        raise SystemExit(cmd_show(args.skill_id))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
