#!/usr/bin/env python3
"""Inspect the harness run/observability artifacts under .aries_harness/runs.

Operationalizes the aries-harness-observability contract: every run report
should carry a `## Runtime links` body section so an operator can trace it back
to its run/task/checkpoint. Reports missing that block are flagged, and the
compliance ratio is reported alongside the broader run-artifact inventory.

This is the observability analog of memory-inspect.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_SECTIONS = ["## Runtime links"]


def validate_run_report(text: str) -> list[str]:
    """Return the required traceability sections missing from a run report body.

    A run report without `## Runtime links` cannot be traced to its run, so it
    fails the observability contract regardless of how good its prose is.
    """
    return [sec for sec in REQUIRED_SECTIONS if sec not in text]


def _artifact_id(text: str, fallback: str) -> str:
    """Read artifact_id from frontmatter; fall back to the file stem."""
    if text.startswith("---\n"):
        body = text[4:]
        end = body.find("\n---\n")
        if end != -1:
            for line in body[:end].splitlines():
                stripped = line.strip()
                if stripped.startswith("artifact_id:"):
                    return stripped.split(":", 1)[1].strip().strip('"')
    return fallback


def relative_to(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def collect_reports(reports_dir: Path, harness_root: Path) -> list[dict]:
    reports: list[dict] = []
    if not reports_dir.is_dir():
        return reports
    for path in sorted(reports_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        reports.append(
            {
                "path": relative_to(path, harness_root),
                "artifact_id": _artifact_id(text, path.stem),
                "missing_sections": validate_run_report(text),
            }
        )
    return reports


def build_report(project_root: Path) -> dict:
    harness_root = project_root / ".aries_harness"
    if not harness_root.is_dir():
        raise FileNotFoundError(f"Missing harness directory: {harness_root}")

    reports_dir = harness_root / "runs" / "reports"
    reports = collect_reports(reports_dir, harness_root)
    compliant = [r for r in reports if not r["missing_sections"]]
    non_compliant = [r for r in reports if r["missing_sections"]]

    # Broader inventory (informational): tests/ and github/ run artifacts.
    inventory: dict[str, int] = {}
    for sub in ("tests", "github", "deployments"):
        sub_dir = harness_root / "runs" / sub
        inventory[sub] = sum(1 for p in sub_dir.glob("*.md") if p.name != "README.md") if sub_dir.is_dir() else 0

    warnings: list[str] = []
    for r in non_compliant:
        warnings.append(
            f"Run report {r['path']} missing traceability section(s): {', '.join(r['missing_sections'])}"
        )

    return {
        "project_root": str(project_root),
        "harness_root": str(harness_root),
        "run_reports": {
            "total": len(reports),
            "compliant": len(compliant),
            "compliance_ratio": round(len(compliant) / len(reports), 4) if reports else 0.0,
            "non_compliant": [{"path": r["path"], "missing_sections": r["missing_sections"]} for r in non_compliant],
        },
        "run_artifact_inventory": inventory,
        "warnings": warnings,
    }


def render_text(report: dict) -> str:
    rr = report["run_reports"]
    lines = [
        f"Run/observability inspection: {report['harness_root']}",
        "",
        "Run reports (observability contract)",
        f"  - compliant: {rr['compliant']} / {rr['total']}  (ratio {rr['compliance_ratio']})",
    ]
    if rr["non_compliant"]:
        lines.append("  - missing runtime-links traceability:")
        for r in rr["non_compliant"]:
            lines.append(f"      - {r['path']}")
    inv = report["run_artifact_inventory"]
    if inv:
        lines.append("")
        lines.append("Run artifact inventory (informational)")
        for k, v in inv.items():
            lines.append(f"  - {k}: {v}")
    lines.append("")
    lines.append("Warnings")
    if report["warnings"]:
        for w in report["warnings"]:
            lines.append(f"  - {w}")
    else:
        lines.append("  - none")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Aries harness run/observability artifacts.")
    parser.add_argument("--project-root", default=".", help="Target project root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a text report.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    try:
        report = build_report(project_root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
