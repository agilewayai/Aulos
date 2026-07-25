#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

META_DEFINE_LAYER = "MetaDefineLayer"
RUN_COOKING_LAYER = "RunCookingLayer"
SHARED_SUPPORT_SURFACE = "SharedSupportSurface"

CANONICAL_ROOT_DOCS = [
    "README.md",
    "INDEX.md",
    "MISSION.md",
    "TASK_STACK.md",
    "PIPELINE.md",
    "STATE.md",
    "JOURNAL.md",
    "EVAL.md",
    "RISKS.md",
    "MEMORY.md",
    "ADR.md",
    "RUNBOOK.md",
]

CANONICAL_ROOT_DESCRIPTIONS = {
    "README.md": "entry point and command hints",
    "INDEX.md": "generated index of root docs and organized collections",
    "MISSION.md": "north star, boundary, and success test",
    "TASK_STACK.md": "active tasks, milestone, blockers, and next slices",
    "PIPELINE.md": "engineering phase ledger from requirements to deployment",
    "STATE.md": "current run state, workspace, and next action",
    "JOURNAL.md": "milestones, failures, and resume hints",
    "EVAL.md": "verification commands and acceptance gate",
    "RISKS.md": "risk and approval boundaries",
    "MEMORY.md": "hot durable memory snapshot and retrieval map",
    "ADR.md": "high-level architecture decisions",
    "RUNBOOK.md": "start, resume, takeover, and rollback notes",
}

ROOT_DOC_LAYERS = {
    "README.md": SHARED_SUPPORT_SURFACE,
    "INDEX.md": SHARED_SUPPORT_SURFACE,
    "MISSION.md": META_DEFINE_LAYER,
    "TASK_STACK.md": RUN_COOKING_LAYER,
    "PIPELINE.md": RUN_COOKING_LAYER,
    "STATE.md": RUN_COOKING_LAYER,
    "JOURNAL.md": RUN_COOKING_LAYER,
    "EVAL.md": META_DEFINE_LAYER,
    "RISKS.md": META_DEFINE_LAYER,
    "MEMORY.md": SHARED_SUPPORT_SURFACE,
    "ADR.md": META_DEFINE_LAYER,
    "RUNBOOK.md": META_DEFINE_LAYER,
}

LAYER_MANIFESTS = {
    META_DEFINE_LAYER: "layers/MetaDefineLayer/README.md",
    RUN_COOKING_LAYER: "layers/RunCookingLayer/README.md",
    SHARED_SUPPORT_SURFACE: "layers/SharedSupportSurface/README.md",
}

MANAGED_DIRS = [
    "layers",
    "layers/MetaDefineLayer",
    "layers/RunCookingLayer",
    "layers/SharedSupportSurface",
    "memory",
    "history",
    "checkpoints",
    "decisions",
    "runs",
    "references",
    "archive",
]

META_DEFINE_COLLECTIONS = {
    "references": "meta-definition collections and reference packs",
    "references/requests": "upstream request briefs and business intent anchors",
    "references/specs": "behavior and acceptance contracts derived from requests",
    "references/stories": "sprintable slices linked to specs and verification",
    "references/domain": "domain analysis and modeling artifacts",
    "references/iterations": "iteration and sprint planning artifacts",
    "references/tasks": "detailed task breakdown and slice maps",
    "references/risks": "detailed risk registers and mitigation notes",
    "decisions": "meta decisions and decision packs",
    "decisions/architecture": "system design and architecture packs",
    "decisions/adrs": "detailed ADR records linked from the root ADR index",
}

RUN_COOKING_COLLECTIONS = {
    "checkpoints": "pause, resume, handoff, and checkpoint artifacts",
    "runs": "run summaries and execution evidence",
    "runs/tests": "test execution and fix evidence",
    "runs/reports": "iteration reports and closeouts",
    "runs/github": "commit, PR, and merge evidence",
    "runs/deployments": "deployment, smoke, and rollback evidence",
}

SHARED_SUPPORT_COLLECTIONS = {
    "layers": "layer manifests and ownership guides",
    "memory": "cold memory maps and durable cards",
    "history": "generated history projections",
    "archive": "retained historical artifacts",
}

PIPELINE_COLLECTIONS = {
    key: value
    for collection in (META_DEFINE_COLLECTIONS, RUN_COOKING_COLLECTIONS)
    for key, value in collection.items()
}

EXTRA_STRUCTURE_DIRS = ["memory/cards"] + list(PIPELINE_COLLECTIONS.keys())
FINGERPRINT_FILE = "ARIES_HARNESS_FINGERPRINT.json"
HARNESS_MANAGER = "aries-harness"
ROOT_FINGERPRINT = "aries-harness/bootstrap-root/v1"
DOC_FINGERPRINT = "aries-harness/bootstrap-doc/v1"
HISTORY_DOC_FINGERPRINT = "aries-harness/history-doc/v1"
EFFECTIVE_STATUSES = {"active", "generated", "archived", "superseded", "draft"}

ROOT_DOC_ROLES = {
    "README.md": "harness-readme",
    "INDEX.md": "harness-index",
    "MISSION.md": "mission",
    "TASK_STACK.md": "task-stack",
    "PIPELINE.md": "engineering-pipeline",
    "STATE.md": "state",
    "JOURNAL.md": "journal",
    "EVAL.md": "evaluation",
    "RISKS.md": "risks",
    "MEMORY.md": "memory",
    "ADR.md": "adr",
    "RUNBOOK.md": "runbook",
}

SPECIAL_DOC_ROLES = {
    "layers/MetaDefineLayer/README.md": "layer-manifest",
    "layers/RunCookingLayer/README.md": "layer-manifest",
    "layers/SharedSupportSurface/README.md": "layer-manifest",
    "memory/INDEX.md": "memory-index",
    "memory/cards/README.md": "memory-cards-readme",
    "history/README.md": "history-readme",
    "history/STATUS.md": "history-status",
    "history/ROADMAP.md": "history-roadmap",
    "history/TIMELINE.md": "history-timeline",
    "history/RETROSPECTIVE.md": "history-retrospective",
    "history/DAILY_SUMMARY_INDEX.md": "history-daily-summary-index",
    "history/DOC_TRACE.md": "history-doc-trace",
    "references/requests/README.md": "pipeline-requests-readme",
    "references/specs/README.md": "pipeline-specs-readme",
    "references/stories/README.md": "pipeline-stories-readme",
    "references/domain/README.md": "pipeline-domain-readme",
    "references/iterations/README.md": "pipeline-iterations-readme",
    "references/tasks/README.md": "pipeline-tasks-readme",
    "references/risks/README.md": "pipeline-risks-readme",
    "decisions/architecture/README.md": "pipeline-architecture-readme",
    "decisions/adrs/README.md": "pipeline-adrs-readme",
    "runs/tests/README.md": "pipeline-tests-readme",
    "runs/reports/README.md": "pipeline-reports-readme",
    "runs/github/README.md": "pipeline-github-readme",
    "runs/deployments/README.md": "pipeline-deployments-readme",
}

PREFIX_DOC_ROLES = [
    ("references/requests/", "business-requirement"),
    ("references/specs/", "spec-package"),
    ("references/stories/", "story-slice-pack"),
    ("references/domain/", "domain-analysis"),
    ("references/iterations/", "iteration-plan"),
    ("references/tasks/", "task-breakdown"),
    ("references/risks/", "risk-register"),
    ("decisions/adrs/", "adr-record"),
    ("decisions/architecture/", "system-design"),
    ("runs/tests/", "test-execution"),
    ("runs/reports/", "iteration-report"),
    ("runs/github/", "github-delivery"),
    ("runs/deployments/", "deployment-evidence"),
    ("runs/", "run-evidence"),
    ("checkpoints/", "checkpoint"),
    ("memory/cards/", "memory-card"),
    ("memory/", "memory-support"),
    ("archive/", "archived-doc"),
]

FRONTMATTER_KEY_ORDER = [
    "schema_version",
    "project_id",
    "owner",
    "artifact_id",
    "doc_role",
    "harness_layer",
    "layer_manifest_for",
    "managed_by",
    "fingerprint",
    "generated_by",
    "initialized_at",
    "generated_at",
    "last_organized_at",
    "status",
    "last_updated_at",
    "completed_at",
    "timebox_actual",
    "effective_status",
    "effective_since",
    "content_fingerprint",
    "trace_history_source",
    "trace_last_commit_sha",
    "trace_last_commit_at",
    "trace_revision_count",
]
VOLATILE_TRACE_KEYS = {
    "content_fingerprint",
    "trace_history_source",
    "trace_last_commit_sha",
    "trace_last_commit_at",
    "trace_revision_count",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reorganize extra Markdown files under .aries_harness and refresh INDEX.md."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Target project root. Defaults to current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without writing files.",
    )
    return parser.parse_args()


def classify_markdown(name: str) -> str:
    lower = name.lower()
    if (
        lower.startswith("memory-")
        or lower.startswith("fact-")
        or lower.startswith("pattern-")
        or lower.startswith("pitfall-")
        or lower.startswith("invariant-")
    ):
        return "memory"
    if (
        lower.startswith("history-")
        or lower.startswith("timeline-")
        or lower.startswith("roadmap-")
        or lower.startswith("status-")
        or lower.startswith("retrospective-")
    ):
        return "history"
    if lower.startswith("req-") or lower.startswith("brd-") or lower.startswith("requirement-"):
        return "references/requests"
    if lower.startswith("spec-") or lower.startswith("spec-package-") or lower.startswith("scope-"):
        return "references/specs"
    if lower.startswith("story-") or lower.startswith("story-slice-") or lower.startswith("epic-"):
        return "references/stories"
    if lower.startswith("dom-") or lower.startswith("domain-") or lower.startswith("model-"):
        return "references/domain"
    if lower.startswith("iter-") or lower.startswith("iteration-plan-") or lower.startswith("sprint-plan-"):
        return "references/iterations"
    if lower.startswith("task-") or lower.startswith("task-breakdown-") or lower.startswith("slice-") or lower.startswith("backlog-"):
        return "references/tasks"
    if lower.startswith("risk-") or lower.startswith("risk-register-") or lower.startswith("mitigation-"):
        return "references/risks"
    if lower.startswith("adr-") or lower.startswith("decision-"):
        return "decisions/adrs"
    if (
        lower.startswith("architecture-")
        or lower.startswith("design-")
        or lower.startswith("arch-")
        or lower.startswith("system-design-")
    ):
        return "decisions/architecture"
    if "checkpoint" in lower or "handoff" in lower or "resume" in lower or lower.startswith("pause-"):
        return "checkpoints"
    if (
        lower.startswith("testrun-")
        or lower.startswith("test-execution-")
        or lower.startswith("fix-")
        or lower.startswith("verification-")
    ):
        return "runs/tests"
    if lower.startswith("report-") or lower.startswith("iteration-report-") or lower.startswith("closeout-"):
        return "runs/reports"
    if lower.startswith("github-") or lower.startswith("pr-") or lower.startswith("commit-") or lower.startswith("merge-"):
        return "runs/github"
    if lower.startswith("deploy-") or lower.startswith("rollout-") or lower.startswith("production-") or lower.startswith("rollback-"):
        return "runs/deployments"
    if lower.startswith("run-") or lower.startswith("candidate-") or lower.startswith("approval-"):
        return "runs"
    if lower.startswith("archive-") or lower.endswith(".old.md") or lower.endswith(".bak.md"):
        return "archive"
    return "references"


def ensure_structure(harness_root: Path, dry_run: bool) -> None:
    if dry_run:
        return
    for directory in MANAGED_DIRS + EXTRA_STRUCTURE_DIRS:
        target = harness_root / directory
        target.mkdir(parents=True, exist_ok=True)
        keep = target / ".gitkeep"
        if directory == "layers" or directory.startswith("layers/"):
            continue
        keep.touch(exist_ok=True)


def parse_frontmatter(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    body = text[4:]
    if "\n---\n" not in body:
        return {}
    frontmatter_text, _ = body.split("\n---\n", 1)
    parsed: dict[str, str] = {}
    for raw_line in frontmatter_text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"')
    return parsed


def split_frontmatter(text: str) -> tuple[dict[str, str], str, bool]:
    if not text.startswith("---\n"):
        return {}, text, False
    body = text[4:]
    if "\n---\n" not in body:
        return {}, text, False
    frontmatter_text, remainder = body.split("\n---\n", 1)
    parsed: dict[str, str] = {}
    for raw_line in frontmatter_text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"')
    return parsed, remainder, True


def expected_layer_for_relative_path(relative_path: str) -> str:
    for layer_name, manifest_path in LAYER_MANIFESTS.items():
        if relative_path == manifest_path:
            return layer_name
    if relative_path in ROOT_DOC_LAYERS:
        return ROOT_DOC_LAYERS[relative_path]
    if relative_path.startswith("memory/") or relative_path.startswith("history/") or relative_path.startswith("archive/"):
        return SHARED_SUPPORT_SURFACE
    if relative_path == "references" or relative_path.startswith("references/"):
        return META_DEFINE_LAYER
    if relative_path == "decisions" or relative_path.startswith("decisions/"):
        return META_DEFINE_LAYER
    if relative_path == "checkpoints" or relative_path.startswith("checkpoints/"):
        return RUN_COOKING_LAYER
    if relative_path == "runs" or relative_path.startswith("runs/"):
        return RUN_COOKING_LAYER
    return ""


def default_effective_status_for_relative_path(relative_path: str) -> str:
    if relative_path == "INDEX.md" or relative_path.startswith("history/"):
        return "generated"
    if relative_path.startswith("archive/"):
        return "archived"
    return "active"


def default_fingerprint_for_relative_path(relative_path: str) -> str:
    if relative_path.startswith("history/"):
        return HISTORY_DOC_FINGERPRINT
    return DOC_FINGERPRINT


def infer_doc_role(relative_path: str) -> str:
    if relative_path in ROOT_DOC_ROLES:
        return ROOT_DOC_ROLES[relative_path]
    if relative_path in SPECIAL_DOC_ROLES:
        return SPECIAL_DOC_ROLES[relative_path]
    if relative_path.startswith("history/daily/") and relative_path.endswith(".md"):
        return "history-daily-summary"
    for prefix, role in PREFIX_DOC_ROLES:
        if relative_path.startswith(prefix):
            return role
    if relative_path.endswith("/README.md"):
        parent = Path(relative_path).parent.name or "managed"
        return f"{parent}-readme"
    return "managed-doc"


def quote_frontmatter_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_frontmatter(frontmatter: dict[str, str]) -> str:
    ordered_keys = [key for key in FRONTMATTER_KEY_ORDER if key in frontmatter]
    ordered_keys.extend(sorted(key for key in frontmatter if key not in FRONTMATTER_KEY_ORDER))
    lines = ["---"]
    for key in ordered_keys:
        lines.append(f"{key}: {quote_frontmatter_value(frontmatter[key])}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def normalized_effective_since(frontmatter: dict[str, str], fallback_timestamp: str) -> str:
    for key in [
        "effective_since",
        "last_updated_at",
        "generated_at",
        "last_organized_at",
        "initialized_at",
    ]:
        value = frontmatter.get(key, "").strip()
        if value:
            return value
    return fallback_timestamp


def git_stdout(project_root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.rstrip("\n")


def git_file_text(project_root: Path, revision: str, repo_relative_path: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "show", f"{revision}:{repo_relative_path}"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout


def normalized_trace_identity(text: str) -> str:
    frontmatter, body, had_frontmatter = split_frontmatter(text)
    if not had_frontmatter:
        return text.rstrip("\n")
    identity_lines = [
        f"{key}={frontmatter[key]}"
        for key in sorted(frontmatter)
        if key not in VOLATILE_TRACE_KEYS
    ]
    return "\n".join(identity_lines + ["---", body.lstrip("\n").rstrip("\n")])


def git_trace_for_repo_path(project_root: Path, repo_relative_path: str) -> dict[str, str]:
    raw = git_stdout(
        project_root,
        "log",
        "--follow",
        "--date=iso-strict",
        "--pretty=format:%H%x09%cI%x09%s",
        "--",
        repo_relative_path,
    )
    if not raw:
        return {
            "trace_history_source": "filesystem-only",
            "trace_last_commit_sha": "",
            "trace_last_commit_at": "",
            "trace_revision_count": "0",
        }

    commits: list[dict[str, str]] = []
    for raw_line in raw.splitlines():
        if not raw_line.strip():
            continue
        parts = raw_line.split("\t", 2)
        commits.append(
            {
                "sha": parts[0] if len(parts) >= 1 else "",
                "date": parts[1] if len(parts) >= 2 else "",
            }
        )

    distinct_revision_count = 0
    current_identity = ""
    current_group_oldest: dict[str, str] | None = None
    last_substantive: dict[str, str] | None = None

    for commit in commits:
        sha = commit.get("sha", "")
        if not sha:
            continue
        text = git_file_text(project_root, sha, repo_relative_path)
        if not text:
            continue
        identity = normalized_trace_identity(text)
        if current_group_oldest is None:
            current_identity = identity
            current_group_oldest = commit
            distinct_revision_count = 1
            continue
        if identity == current_identity:
            current_group_oldest = commit
            continue
        if last_substantive is None:
            last_substantive = current_group_oldest
        current_identity = identity
        current_group_oldest = commit
        distinct_revision_count += 1

    target = last_substantive or current_group_oldest
    if target is None:
        return {
            "trace_history_source": "filesystem-only",
            "trace_last_commit_sha": "",
            "trace_last_commit_at": "",
            "trace_revision_count": "0",
        }

    return {
        "trace_history_source": "git",
        "trace_last_commit_sha": target.get("sha", ""),
        "trace_last_commit_at": target.get("date", ""),
        "trace_revision_count": str(distinct_revision_count),
    }


def content_fingerprint_for_body(body: str) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def normalize_markdown_file(
    path: Path,
    harness_root: Path,
    project_root: Path,
    fingerprint: dict[str, str],
    fallback_timestamp: str,
    dry_run: bool,
) -> bool:
    relative_path = str(path.relative_to(harness_root))
    repo_relative_path = f".aries_harness/{relative_path}"
    original_text = path.read_text(encoding="utf-8")
    current_frontmatter, body, had_frontmatter = split_frontmatter(original_text)
    normalized = dict(current_frontmatter)

    normalized.setdefault("schema_version", "0.1")
    normalized.setdefault("project_id", fingerprint["project_id"])
    normalized.setdefault("owner", fingerprint["owner"])
    normalized.setdefault("doc_role", infer_doc_role(relative_path))

    expected_layer = expected_layer_for_relative_path(relative_path)
    if expected_layer:
        normalized["harness_layer"] = expected_layer

    normalized.setdefault("managed_by", HARNESS_MANAGER)
    normalized.setdefault("fingerprint", default_fingerprint_for_relative_path(relative_path))
    normalized.setdefault(
        "initialized_at",
        current_frontmatter.get("generated_at")
        or current_frontmatter.get("last_updated_at")
        or fallback_timestamp,
    )

    effective_status = normalized.get("effective_status", "").strip().casefold()
    if effective_status not in EFFECTIVE_STATUSES:
        normalized["effective_status"] = default_effective_status_for_relative_path(relative_path)
    normalized["effective_since"] = normalized_effective_since(normalized, fallback_timestamp)
    normalized["content_fingerprint"] = content_fingerprint_for_body(body.lstrip("\n"))
    normalized.update(git_trace_for_repo_path(project_root, repo_relative_path))

    rendered = render_frontmatter(normalized) + body.lstrip("\n")
    if had_frontmatter and not body.endswith("\n") and not rendered.endswith("\n"):
        rendered += "\n"
    elif not had_frontmatter and not original_text.endswith("\n") and not rendered.endswith("\n"):
        rendered += "\n"
    elif original_text.endswith("\n") and not rendered.endswith("\n"):
        rendered += "\n"

    if rendered == original_text:
        return False
    if not dry_run:
        path.write_text(rendered, encoding="utf-8")
    return True


def normalize_managed_markdown_docs(
    project_root: Path,
    harness_root: Path,
    fingerprint: dict[str, str],
    dry_run: bool,
) -> list[str]:
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    changed: list[str] = []
    for path in sorted(harness_root.rglob("*.md")):
        if not path.is_file():
            continue
        relative_path = str(path.relative_to(harness_root))
        if normalize_markdown_file(path, harness_root, project_root, fingerprint, timestamp, dry_run):
            changed.append(relative_path)
    return changed


def infer_identity(harness_root: Path, project_root: Path) -> dict[str, str]:
    defaults = {
        "project_id": project_root.name,
        "owner": "operator",
        "initialized_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    for candidate in [
        harness_root / "README.md",
        harness_root / "MISSION.md",
        harness_root / "STATE.md",
        harness_root / "INDEX.md",
    ]:
        frontmatter = parse_frontmatter(candidate)
        if not frontmatter:
            continue
        if frontmatter.get("project_id"):
            defaults["project_id"] = frontmatter["project_id"]
        if frontmatter.get("owner"):
            defaults["owner"] = frontmatter["owner"]
        if frontmatter.get("initialized_at"):
            defaults["initialized_at"] = frontmatter["initialized_at"]
        break
    return defaults


def build_fingerprint_payload(project_root: Path, identity: dict[str, str]) -> dict:
    return {
        "schema_version": "0.1",
        "managed_by": HARNESS_MANAGER,
        "fingerprint": ROOT_FINGERPRINT,
        "generated_by": "/aries-harness init",
        "root_dir": ".aries_harness",
        "project_id": identity["project_id"],
        "owner": identity["owner"],
        "initialized_at": identity["initialized_at"],
        "canonical_commands": [
            "/aries-harness init",
            "/aries-harness well-organized",
            "/aries-harness pipeline-inspect",
            "/aries-harness memory-inspect",
            "/aries-harness history-refresh",
            "/aries-harness history-status",
        ],
        "markdown_fingerprint": {
            "managed_by": HARNESS_MANAGER,
            "fingerprint": DOC_FINGERPRINT,
        },
        "document_governance": {
            "required_frontmatter": [
                "harness_layer",
                "managed_by",
                "fingerprint",
                "effective_status",
                "effective_since",
                "content_fingerprint",
                "trace_history_source",
                "trace_last_commit_sha",
                "trace_last_commit_at",
                "trace_revision_count",
            ],
            "default_effective_status": {
                "canonical_docs": "active",
                "history_surface": "generated",
                "archive": "archived",
            },
            "trace_history_source": {
                "git_repository": "git",
                "non_git_project": "filesystem-only",
            },
            "trace_outputs": [
                "history/DOC_TRACE.md",
                "history/doc-trace.json",
            ],
            "closeout_fields_for_ready_phase_artifacts": [
                "completed_at",
                "timebox_actual",
                "Closeout timing section",
            ],
        },
        "layer_model": {
            "strategy": "compatibility-dual-layer-with-shared-support",
            "meta_define_layer": {
                "root_docs": [name for name, layer in ROOT_DOC_LAYERS.items() if layer == META_DEFINE_LAYER],
                "managed_directories": list(META_DEFINE_COLLECTIONS.keys()),
            },
            "run_cooking_layer": {
                "root_docs": [name for name, layer in ROOT_DOC_LAYERS.items() if layer == RUN_COOKING_LAYER],
                "managed_directories": list(RUN_COOKING_COLLECTIONS.keys()),
            },
            "shared_support_surface": {
                "root_docs": [name for name, layer in ROOT_DOC_LAYERS.items() if layer == SHARED_SUPPORT_SURFACE],
                "managed_directories": ["layers", "memory", "memory/cards", "history", "archive"],
            },
        },
    }


def load_or_prepare_fingerprint(harness_root: Path, project_root: Path) -> tuple[dict, bool]:
    fingerprint_path = harness_root / FINGERPRINT_FILE
    if fingerprint_path.is_file():
        try:
            raw = json.loads(fingerprint_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                identity = {
                    "project_id": str(raw.get("project_id") or project_root.name),
                    "owner": str(raw.get("owner") or "operator"),
                    "initialized_at": str(
                        raw.get("initialized_at")
                        or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
                    ),
                }
                normalized = build_fingerprint_payload(project_root, identity)
                return normalized, normalized != raw
        except json.JSONDecodeError:
            pass

    identity = infer_identity(harness_root, project_root)
    return build_fingerprint_payload(project_root, identity), True


def planned_moves(harness_root: Path) -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []
    for entry in sorted(harness_root.iterdir(), key=lambda item: item.name.lower()):
        if entry.is_dir():
            continue
        if entry.suffix.lower() != ".md":
            continue
        if entry.name in CANONICAL_ROOT_DOCS:
            continue
        destination = harness_root / classify_markdown(entry.name) / entry.name
        moves.append((entry, destination))
    return moves


def render_layer_section(
    harness_root: Path,
    title: str,
    root_docs: list[str],
    collections: dict[str, str],
) -> list[str]:
    lines = [f"## {title}", ""]
    lines.append("### Root docs")
    for filename in root_docs:
        path = harness_root / filename
        if path.exists():
            lines.append(f"- [{filename}]({filename})")
            lines.append(f"  {CANONICAL_ROOT_DESCRIPTIONS[filename]}")
    lines.extend(["", "### Managed collections", ""])
    for directory, description in collections.items():
        lines.append(f"#### `{directory}/`")
        lines.append(f"- role: {description}")
        items = sorted(
            path.name
            for path in (harness_root / directory).glob("*.md")
            if path.is_file()
        )
        if items:
            for item in items:
                lines.append(f"- [{item}]({directory}/{item})")
        else:
            lines.append("- none")
        lines.append("")
    return lines


def render_index(harness_root: Path, fingerprint: dict) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "---",
        'schema_version: "0.1"',
        f'project_id: "{fingerprint["project_id"]}"',
        f'owner: "{fingerprint["owner"]}"',
        'doc_role: "harness-index"',
        f'harness_layer: "{SHARED_SUPPORT_SURFACE}"',
        f'managed_by: "{HARNESS_MANAGER}"',
        f'fingerprint: "{DOC_FINGERPRINT}"',
        'generated_by: "/aries-harness well-organized"',
        f'initialized_at: "{fingerprint["initialized_at"]}"',
        f'last_organized_at: "{timestamp}"',
        'effective_status: "generated"',
        f'effective_since: "{timestamp}"',
        "---",
        "",
        "# Harness Index",
        "",
        f"Last organized: `{timestamp}`",
        "",
        "Canonical spelling: `/aries-harness well-organized`",
        "",
        f"Fingerprint marker: `{HARNESS_MANAGER}` / `{DOC_FINGERPRINT}`",
        "",
        "## Layer manifests",
        "",
    ]
    for layer_name, rel_path in LAYER_MANIFESTS.items():
        path = harness_root / rel_path
        if path.exists():
            lines.append(f"- [{layer_name}]({rel_path})")
        else:
            lines.append(f"- {layer_name}: missing `{rel_path}`")
    lines.extend(
        [
            "",
            "## Layer model",
            "",
            f"- `{META_DEFINE_LAYER}` defines stable mission, architecture, gates, risk policy, and planning truth",
            f"- `{RUN_COOKING_LAYER}` carries the live execution stack, progression state, checkpoints, and delivery evidence",
            f"- `{SHARED_SUPPORT_SURFACE}` provides shared entry docs, memory, generated history, and archive material",
            "",
        ]
    )
    lines.extend(
        render_layer_section(
            harness_root,
            META_DEFINE_LAYER,
            [name for name, layer in ROOT_DOC_LAYERS.items() if layer == META_DEFINE_LAYER],
            META_DEFINE_COLLECTIONS,
        )
    )
    lines.extend(
        render_layer_section(
            harness_root,
            RUN_COOKING_LAYER,
            [name for name, layer in ROOT_DOC_LAYERS.items() if layer == RUN_COOKING_LAYER],
            RUN_COOKING_COLLECTIONS,
        )
    )
    lines.extend(
        render_layer_section(
            harness_root,
            SHARED_SUPPORT_SURFACE,
            [name for name, layer in ROOT_DOC_LAYERS.items() if layer == SHARED_SUPPORT_SURFACE],
            SHARED_SUPPORT_COLLECTIONS,
        )
    )
    lines.extend(
        [
            "## Command reminders",
            "",
            "- `/aries-harness init` creates the stable skeleton.",
            "- `/aries-harness well-organized` keeps the root high-signal and moves extra Markdown into managed collections.",
            "- `/aries-harness pipeline-inspect` checks the engineering pipeline phase ledger, layer markers, artifact paths, and gate coverage.",
            "- `/aries-harness memory-inspect` checks hot-memory size, cold-memory cards, and stale memory hygiene.",
            "- `/aries-harness history-refresh` regenerates readable status, roadmap, timeline, retrospective, daily-summary, and doc-trace docs under `history/`.",
            "- `/aries-harness history-status` prints the same history model as a quick terminal or JSON snapshot.",
            "",
            "## Organization rules",
            "",
            "- keep canonical recovery docs in the root",
            "- keep `MetaDefineLayer` and `RunCookingLayer` semantically separated even when root entry docs coexist",
            "- move extra run, checkpoint, and design notes under managed collections",
            "- do not delete Markdown files during organization",
            "",
            "## Document governance",
            "",
            "- every managed Markdown file should declare `effective_status`, `effective_since`, `content_fingerprint`, and git-backed trace fields when history exists",
            "- canonical docs default to `active`; generated history surfaces default to `generated`; archived material defaults to `archived`",
            "- richer per-doc trace fields are `trace_history_source`, `trace_last_commit_sha`, `trace_last_commit_at`, and `trace_revision_count`",
            "- when a closeout-critical phase artifact becomes `done` or `validated`, record `completed_at`, `timebox_actual`, and a `Closeout timing` section instead of relying on `last_updated_at` alone",
            "- use `history/DOC_TRACE.md` and `history/doc-trace.json` for the readable and machine-readable document trace",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    harness_root = project_root / ".aries_harness"

    if not harness_root.is_dir():
        print(
            f"Missing harness directory: {harness_root}\nRun /aries-harness init first.",
            file=sys.stderr,
        )
        return 1

    ensure_structure(harness_root, dry_run=args.dry_run)
    moves = planned_moves(harness_root)
    fingerprint, fingerprint_needs_write = load_or_prepare_fingerprint(harness_root, project_root)

    collisions = [dest for _, dest in moves if dest.exists()]
    if collisions:
        print("Refusing to organize because destination paths already exist:", file=sys.stderr)
        for path in collisions:
            print(f"  {path}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Would organize {harness_root}")
        if moves:
            for src, dest in moves:
                print(f"  move {src.name} -> {dest.relative_to(harness_root)}")
        else:
            print("  no extra root Markdown files to move")
        if fingerprint_needs_write:
            print(f"  ensure {FINGERPRINT_FILE}")
        normalized_paths = normalize_managed_markdown_docs(project_root, harness_root, fingerprint, dry_run=True)
        if normalized_paths:
            for relative_path in normalized_paths:
                print(f"  normalize {relative_path}")
        else:
            print("  all managed Markdown already matches the governance contract")
        print("  refresh INDEX.md with layer topology")
        return 0

    if fingerprint_needs_write:
        fingerprint_path = harness_root / FINGERPRINT_FILE
        fingerprint_path.write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")

    for src, dest in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)

    normalized_paths = normalize_managed_markdown_docs(project_root, harness_root, fingerprint, dry_run=False)
    index_path = harness_root / "INDEX.md"
    index_path.write_text(render_index(harness_root, fingerprint), encoding="utf-8")
    index_timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    if normalize_markdown_file(
        index_path,
        harness_root,
        project_root,
        fingerprint,
        index_timestamp,
        dry_run=False,
    ) and "INDEX.md" not in normalized_paths:
        normalized_paths.append("INDEX.md")

    print(f"Organized {harness_root}")
    if moves:
        for src, dest in moves:
            print(f"  moved {src.name} -> {dest.relative_to(harness_root)}")
    else:
        print("  no extra root Markdown files needed moving")
    if fingerprint_needs_write:
        print(f"  wrote {FINGERPRINT_FILE}")
    if normalized_paths:
        for relative_path in normalized_paths:
            print(f"  normalized {relative_path}")
    else:
        print("  all managed Markdown already matched the governance contract")
    print("  refreshed INDEX.md with layer topology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
