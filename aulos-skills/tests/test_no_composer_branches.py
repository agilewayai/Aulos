"""Contract: skill runtime/identity must not grow composer-name code branches."""

from __future__ import annotations

import ast
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src" / "aulos_skills"
_SCAN = ("runtime.py", "identity.py", "ambient_agent.py", "guide_render.py", "salon_codex.py")

# Composer proper names that must never appear in If/Compare tests.
_BANNED_IN_CONDITIONS = {
    "chopin",
    "肖邦",
    "bach",
    "巴赫",
    "beethoven",
    "贝多芬",
    "mahler",
    "马勒",
    "mozart",
    "莫扎特",
    "goldberg",
    "哥德堡",
}


def _string_consts(node: ast.AST) -> list[str]:
    out: list[str] = []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        out.append(node.value)
    for child in ast.iter_child_nodes(node):
        out.extend(_string_consts(child))
    return out


def test_no_composer_name_conditionals_in_skill_core() -> None:
    hits: list[str] = []
    for name in _SCAN:
        path = _SRC / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.If, ast.IfExp, ast.Assert, ast.Match)):
                continue
            # Only inspect the test / subject — body may mention composers in comments/docs via strings elsewhere
            targets: list[ast.AST] = []
            if isinstance(node, ast.If):
                targets = [node.test]
            elif isinstance(node, ast.IfExp):
                targets = [node.test]
            elif isinstance(node, ast.Assert):
                targets = [node.test]
            elif isinstance(node, ast.Match):
                targets = [node.subject]
            for t in targets:
                for s in _string_consts(t):
                    low = s.lower()
                    for banned in _BANNED_IN_CONDITIONS:
                        if banned.lower() in low or banned in s:
                            hits.append(f"{name}:{getattr(node, 'lineno', '?')}:{s!r}")
    assert not hits, "composer-name conditionals found:\n" + "\n".join(hits)


def test_character_dance_family_has_no_composer_locked_search_urls() -> None:
    """Form scaffolds must not embed a single-composer media shelf."""
    path = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "aulos-listening-synthesize"
        / "assets"
        / "families"
        / "character-dance-piano.yaml"
    )
    text = path.read_text(encoding="utf-8")
    for banned in ("Chopin+", "Chopin%", "search_query=Chopin", "q=Chopin"):
        assert banned not in text, f"composer-locked search URL: {banned}"
