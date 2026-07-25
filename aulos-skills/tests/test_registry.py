from pathlib import Path

from aulos_skills.config import Settings
from aulos_skills.registry import discover_skills, load_manifest


def test_load_manifest(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "skill.yaml").write_text(
        "id: demo\nname: Demo\nsummary: hi\nlayer: core\nversion: 0.1.0\n",
        encoding="utf-8",
    )
    manifest = load_manifest(skill_dir)
    assert manifest is not None
    assert manifest.skill_id == "demo"
    assert manifest.name == "Demo"


def test_discover_bundled_skills() -> None:
    root = Path(__file__).resolve().parents[1]
    skills = discover_skills([root / "skills"])
    ids = {s.skill_id for s in skills}
    assert "aulos-core" in ids
    assert "aulos-service-bootstrap" in ids
    assert "aulos-ops-observability" in ids
    assert "aulos-operating-defaults" in ids


def test_settings_roots(tmp_path: Path) -> None:
    settings = Settings(include_bundled=True, skills_root=str(tmp_path))
    roots = settings.resolved_roots(Path(__file__).resolve().parents[1])
    assert any(r.name == "skills" for r in roots)
    assert tmp_path.resolve() in roots
