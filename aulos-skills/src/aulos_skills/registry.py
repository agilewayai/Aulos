from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    name: str
    summary: str
    layer: str
    path: Path
    version: str = "0.1.0"


def load_manifest(skill_dir: Path) -> SkillManifest | None:
    manifest_path = skill_dir / "skill.yaml"
    if not manifest_path.is_file():
        return None
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    skill_id = str(data.get("id") or skill_dir.name)
    return SkillManifest(
        skill_id=skill_id,
        name=str(data.get("name") or skill_id),
        summary=str(data.get("summary") or ""),
        layer=str(data.get("layer") or "core"),
        path=skill_dir,
        version=str(data.get("version") or "0.1.0"),
    )


def discover_skills(roots: list[Path]) -> list[SkillManifest]:
    found: dict[str, SkillManifest] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            manifest = load_manifest(child)
            if manifest is None:
                continue
            found[manifest.skill_id] = manifest
    return list(found.values())
