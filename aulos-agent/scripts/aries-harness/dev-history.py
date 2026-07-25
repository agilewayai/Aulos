#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HARNESS_MANAGER = "aries-harness"
ROOT_FINGERPRINT = "aries-harness/bootstrap-root/v1"
BOOTSTRAP_DOC_FINGERPRINT = "aries-harness/bootstrap-doc/v1"
HISTORY_DOC_FINGERPRINT = "aries-harness/history-doc/v1"
META_DEFINE_LAYER = "MetaDefineLayer"
RUN_COOKING_LAYER = "RunCookingLayer"
SHARED_SUPPORT_SURFACE = "SharedSupportSurface"
FINGERPRINT_FILE = "ARIES_HARNESS_FINGERPRINT.json"
HISTORY_DIRNAME = "history"
HISTORY_DOCS = [
    "README.md",
    "STATUS.md",
    "ROADMAP.md",
    "TIMELINE.md",
    "RETROSPECTIVE.md",
    "DAILY_SUMMARY_INDEX.md",
    "DOC_TRACE.md",
    "doc-trace.json",
    "summary.json",
]
DAILY_SUMMARY_DIRNAME = "daily"
CANONICAL_COMMANDS = [
    "/aries-harness init",
    "/aries-harness well-organized",
    "/aries-harness pipeline-inspect",
    "/aries-harness memory-inspect",
    "/aries-harness history-refresh",
    "/aries-harness history-status",
]
DEFAULT_COMMIT_LIMIT = 12
DEFAULT_JOURNAL_LIMIT = 8
DEFAULT_DAILY_COMMIT_LIMIT = 3
DEFAULT_DAILY_JOURNAL_HEADING_LIMIT = 8
DEFAULT_DAILY_JOURNAL_ITEM_LIMIT = 6
DEFAULT_DAILY_FEATURE_LIMIT = 8
DEFAULT_WORKING_TREE_HINT_LIMIT = 8
PLACEHOLDER_SNIPPETS = [
    "define the project target here",
    "define what is in scope",
    "define what is explicitly out of scope",
    "define what counts as done",
    "list actions that require human confirmation",
    "record only stable constraints",
    "runtime quirks:",
    "local setup caveats:",
    "note stable operator or project preferences here",
    "candidate facts to verify before promoting into durable cards:",
    "define the minimum verification gate here",
]

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

DOC_TRACE_LIMIT = 3
TRACE_HISTORY_SOURCES = {"git", "filesystem-only"}
FRONTMATTER_KEY_ORDER = [
    "schema_version",
    "project_id",
    "owner",
    "doc_role",
    "harness_layer",
    "managed_by",
    "fingerprint",
    "generated_by",
    "initialized_at",
    "generated_at",
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
        description="Generate or inspect the Aries harness development-history surface."
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    refresh = subparsers.add_parser(
        "refresh",
        help="Generate .aries_harness/history/ docs from harness state and git evidence.",
    )
    status = subparsers.add_parser(
        "status",
        help="Print a concise status view from the same history evidence model.",
    )

    for subparser in (refresh, status):
        subparser.add_argument(
            "--project-root",
            default=".",
            help="Target project root. Defaults to current directory.",
        )
        subparser.add_argument(
            "--commit-limit",
            type=int,
            default=DEFAULT_COMMIT_LIMIT,
            help=f"Maximum recent git commits to include. Defaults to {DEFAULT_COMMIT_LIMIT}.",
        )
        subparser.add_argument(
            "--journal-limit",
            type=int,
            default=DEFAULT_JOURNAL_LIMIT,
            help=f"Maximum recent journal entries to include. Defaults to {DEFAULT_JOURNAL_LIMIT}.",
        )
        subparser.add_argument(
            "--json",
            action="store_true",
            help="Emit machine-readable JSON instead of a text report.",
        )

    refresh.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be refreshed without writing files.",
    )
    return parser.parse_args()


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    body = text[4:]
    if "\n---\n" not in body:
        return text
    _, remainder = body.split("\n---\n", 1)
    return remainder


def split_frontmatter_text(text: str) -> tuple[dict[str, str], str, bool]:
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
    current_key: str | None = None
    current_list: list[str] = []

    def flush_current_list() -> None:
        nonlocal current_key, current_list
        if current_key is not None and current_list:
            parsed[current_key] = ", ".join(current_list)
        current_key = None
        current_list = []

    for raw_line in frontmatter_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key is not None:
            current_list.append(stripped[2:].strip().strip('"'))
            continue
        flush_current_list()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            parsed[key] = value.strip('"')
        else:
            current_key = key
            current_list = []
    flush_current_list()
    return parsed


def parse_sections(path: Path) -> dict[str, list[str]]:
    if not path.is_file():
        return {}
    text = strip_frontmatter(path.read_text(encoding="utf-8"))
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        if raw_line.startswith("## "):
            current = raw_line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(raw_line.rstrip())
    return sections


def relative_to(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


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


def content_fingerprint_for_body(body: str) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def clean_item(text: str) -> str:
    return " ".join(text.split())


def collect_bullets(lines: list[str]) -> list[dict[str, object]]:
    bullets: list[dict[str, object]] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("- [x] "):
            bullets.append({"text": clean_item(stripped[6:]), "checked": True})
        elif stripped.startswith("- [ ] "):
            bullets.append({"text": clean_item(stripped[6:]), "checked": False})
        elif stripped.startswith("- "):
            bullets.append({"text": clean_item(stripped[2:]), "checked": None})
    return bullets


def bullet_texts(lines: list[str]) -> list[str]:
    return [item["text"] for item in collect_bullets(lines) if item.get("text")]


def filter_placeholder_items(items: list[str]) -> list[str]:
    filtered: list[str] = []
    for item in items:
        lowered = item.strip().lower()
        if any(snippet in lowered for snippet in PLACEHOLDER_SNIPPETS):
            continue
        filtered.append(item)
    return filtered


def nonempty_or_default(items: list[str], default: str) -> list[str]:
    filtered = filter_placeholder_items(items)
    return filtered if filtered else [default]


def first_or_default(items: list[str], default: str) -> str:
    filtered = filter_placeholder_items(items)
    return filtered[0] if filtered else default


def run_command(project_root: Path, *command: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return 127, ""
    stdout = completed.stdout.rstrip("\n")
    return completed.returncode, stdout


def git_stdout(project_root: Path, *args: str) -> str:
    code, stdout = run_command(project_root, "git", *args)
    return stdout if code == 0 else ""


def git_file_text(project_root: Path, revision: str, relative_path: str) -> str:
    code, stdout = run_command(project_root, "git", "show", f"{revision}:{relative_path}")
    return stdout if code == 0 else ""


def git_available(project_root: Path) -> bool:
    return bool(git_stdout(project_root, "rev-parse", "--show-toplevel"))


def recent_commits(project_root: Path, limit: int) -> list[dict[str, str]]:
    raw = git_stdout(
        project_root,
        "log",
        f"-n{limit}",
        "--date=short",
        "--pretty=format:%h%x09%ad%x09%s",
    )
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def all_commits(project_root: Path) -> list[dict[str, str]]:
    raw = git_stdout(
        project_root,
        "log",
        "--date=short",
        "--pretty=format:%h%x09%ad%x09%s",
    )
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def file_commit_trace(project_root: Path, relative_path: str, limit: int) -> list[dict[str, str]]:
    raw = git_stdout(
        project_root,
        "log",
        "--follow",
        f"-n{limit}",
        "--date=short",
        "--pretty=format:%h%x09%ad%x09%s",
        "--",
        relative_path,
    )
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def normalized_trace_identity(text: str) -> str:
    frontmatter, body, had_frontmatter = split_frontmatter_text(text)
    if not had_frontmatter:
        return text.rstrip("\n")
    identity_lines = [
        f"{key}={frontmatter[key]}"
        for key in sorted(frontmatter)
        if key not in VOLATILE_TRACE_KEYS
    ]
    return "\n".join(identity_lines + ["---", body.lstrip("\n").rstrip("\n")])


def observed_git_trace(project_root: Path, relative_path: str) -> dict[str, str]:
    raw = git_stdout(
        project_root,
        "log",
        "--follow",
        "--date=iso-strict",
        "--pretty=format:%H%x09%cI%x09%s",
        "--",
        relative_path,
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
        text = git_file_text(project_root, sha, relative_path)
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


def working_tree(project_root: Path) -> dict[str, object]:
    raw = git_stdout(project_root, "status", "--porcelain=v1", "--untracked-files=all")
    changes: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        status = (line[:2].strip() or "??").replace(" ", "")
        path = line[3:].strip()
        changes.append({"status": status, "path": path})
    return {
        "clean": len(changes) == 0,
        "change_count": len(changes),
        "changes": changes,
    }


def infer_identity(harness_root: Path, project_root: Path) -> dict[str, str]:
    marker = harness_root / FINGERPRINT_FILE
    if marker.is_file():
        try:
            raw = json.loads(marker.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {
                    "project_id": str(raw.get("project_id") or project_root.name),
                    "owner": str(raw.get("owner") or "operator"),
                    "initialized_at": str(
                        raw.get("initialized_at")
                        or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
                    ),
                }
        except json.JSONDecodeError:
            pass

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


def build_fingerprint_payload(project_root: Path, identity: dict[str, str]) -> dict[str, object]:
    return {
        "schema_version": "0.1",
        "managed_by": HARNESS_MANAGER,
        "fingerprint": ROOT_FINGERPRINT,
        "generated_by": "/aries-harness init",
        "root_dir": ".aries_harness",
        "project_id": identity["project_id"],
        "owner": identity["owner"],
        "initialized_at": identity["initialized_at"],
        "canonical_commands": CANONICAL_COMMANDS,
        "markdown_fingerprint": {
            "managed_by": HARNESS_MANAGER,
            "fingerprint": BOOTSTRAP_DOC_FINGERPRINT,
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
        },
        "layer_model": {
            "strategy": "compatibility-dual-layer-with-shared-support",
            "meta_define_layer": {
                "root_docs": ["MISSION.md", "ADR.md", "RUNBOOK.md", "EVAL.md", "RISKS.md"],
                "managed_directories": [
                    "references",
                    "references/requests",
                    "references/specs",
                    "references/stories",
                    "references/domain",
                    "references/iterations",
                    "references/tasks",
                    "references/risks",
                    "decisions",
                    "decisions/architecture",
                    "decisions/adrs",
                ],
            },
            "run_cooking_layer": {
                "root_docs": ["TASK_STACK.md", "PIPELINE.md", "STATE.md", "JOURNAL.md"],
                "managed_directories": [
                    "checkpoints",
                    "runs",
                    "runs/tests",
                    "runs/reports",
                    "runs/github",
                    "runs/deployments",
                ],
            },
            "shared_support_surface": {
                "root_docs": ["README.md", "INDEX.md", "MEMORY.md"],
                "managed_directories": [
                    "layers",
                    "memory",
                    "memory/cards",
                    "history",
                    "archive",
                ],
            },
        },
    }


def normalize_fingerprint(harness_root: Path, project_root: Path) -> tuple[dict[str, object], bool]:
    identity = infer_identity(harness_root, project_root)
    normalized = build_fingerprint_payload(project_root, identity)
    marker = harness_root / FINGERPRINT_FILE
    if not marker.is_file():
        return normalized, True
    try:
        current = json.loads(marker.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return normalized, True
    return normalized, current != normalized


def build_doc_trace(
    project_root: Path,
    harness_root: Path,
    working_tree_state: dict[str, object],
) -> dict[str, object]:
    dirty_paths = {str(change["path"]) for change in working_tree_state["changes"]}
    documents: list[dict[str, object]] = []
    by_layer: dict[str, int] = {}
    by_effective_status: dict[str, int] = {}
    docs_with_issues = 0

    for path in sorted(harness_root.rglob("*.md")):
        if not path.is_file():
            continue
        relative_path = relative_to(path, harness_root)
        repo_relative_path = f".aries_harness/{relative_path}"
        frontmatter = parse_frontmatter(path)
        commits = file_commit_trace(project_root, repo_relative_path, DOC_TRACE_LIMIT)
        observed_trace = observed_git_trace(project_root, repo_relative_path)
        expected_layer = expected_layer_for_relative_path(relative_path)
        body = strip_frontmatter(path.read_text(encoding="utf-8")).lstrip("\n")
        observed_content_fingerprint = content_fingerprint_for_body(body)
        effective_status = (
            frontmatter.get("effective_status")
            or default_effective_status_for_relative_path(relative_path)
        )
        effective_since = (
            frontmatter.get("effective_since")
            or frontmatter.get("last_updated_at")
            or frontmatter.get("generated_at")
            or frontmatter.get("last_organized_at")
            or frontmatter.get("initialized_at")
            or "not set"
        )
        dirty = repo_relative_path in dirty_paths
        issues: list[str] = []
        if not frontmatter.get("effective_status"):
            issues.append("missing effective_status")
        if not frontmatter.get("effective_since"):
            issues.append("missing effective_since")
        if not frontmatter.get("managed_by"):
            issues.append("missing managed_by")
        if not frontmatter.get("fingerprint"):
            issues.append("missing fingerprint")
        if frontmatter.get("content_fingerprint") != observed_content_fingerprint:
            issues.append("content_fingerprint does not match current body")
        if frontmatter.get("trace_history_source") not in TRACE_HISTORY_SOURCES:
            issues.append("missing or invalid trace_history_source")
        elif effective_status != "generated" and frontmatter.get("trace_history_source") != observed_trace["trace_history_source"]:
            issues.append("trace_history_source does not match observed history source")
        if effective_status != "generated":
            if frontmatter.get("trace_last_commit_sha", "") != observed_trace["trace_last_commit_sha"]:
                issues.append("trace_last_commit_sha does not match observed latest commit")
            if frontmatter.get("trace_last_commit_at", "") != observed_trace["trace_last_commit_at"]:
                issues.append("trace_last_commit_at does not match observed latest commit date")
            if frontmatter.get("trace_revision_count", "") != observed_trace["trace_revision_count"]:
                issues.append("trace_revision_count does not match observed revision count")
        if expected_layer and not frontmatter.get("harness_layer"):
            issues.append("missing harness_layer")
        if issues:
            docs_with_issues += 1

        by_layer[expected_layer or "unclassified"] = by_layer.get(expected_layer or "unclassified", 0) + 1
        by_effective_status[effective_status] = by_effective_status.get(effective_status, 0) + 1

        documents.append(
            {
                "path": relative_path,
                "repo_path": repo_relative_path,
                "doc_role": frontmatter.get("doc_role", "not set"),
                "layer": expected_layer or frontmatter.get("harness_layer", ""),
                "declared_layer": frontmatter.get("harness_layer", ""),
                "effective_status": effective_status,
                "effective_since": effective_since,
                "managed_by": frontmatter.get("managed_by", ""),
                "fingerprint": frontmatter.get("fingerprint", ""),
                "last_updated_at": frontmatter.get("last_updated_at", ""),
                "completed_at": frontmatter.get("completed_at", ""),
                "timebox_actual": frontmatter.get("timebox_actual", ""),
                "content_fingerprint": frontmatter.get("content_fingerprint", ""),
                "observed_content_fingerprint": observed_content_fingerprint,
                "trace_history_source": frontmatter.get("trace_history_source", ""),
                "trace_last_commit_sha": frontmatter.get("trace_last_commit_sha", ""),
                "trace_last_commit_at": frontmatter.get("trace_last_commit_at", ""),
                "trace_revision_count": frontmatter.get("trace_revision_count", ""),
                "observed_trace": observed_trace,
                "latest_commit": commits[0] if commits else None,
                "recent_updates": commits,
                "dirty": dirty,
                "issue_count": len(issues),
                "issues": issues,
            }
        )

    return {
        "summary": {
            "document_count": len(documents),
            "docs_with_issues": docs_with_issues,
            "dirty_docs": sum(1 for doc in documents if doc["dirty"]),
            "by_layer": by_layer,
            "by_effective_status": by_effective_status,
        },
        "documents": documents,
    }


def recent_journal_entries(journal_sections: dict[str, list[str]], limit: int) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for heading, lines in journal_sections.items():
        items = bullet_texts(lines)
        if not items:
            continue
        entries.append({"heading": heading, "items": items})
    if limit <= 0:
        return []
    return entries[:limit]


def date_key_from_timestampish(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if "T" in text:
        return text.split("T", 1)[0]
    return text[:10] if len(text) >= 10 else text


def build_daily_summaries(
    report: dict[str, object],
    commit_limit: int,
    journal_limit: int,
) -> list[dict[str, object]]:
    journal_entries = report["journal"]["all_entries"]
    git_commits = report["git"]["all_commits"]
    by_day: dict[str, dict[str, object]] = {}

    def ensure_day(date_key: str) -> dict[str, object]:
        if date_key not in by_day:
            by_day[date_key] = {
                "date": date_key,
                "journal_headings": [],
                "journal_items": [],
                "feature_evolution": [],
                "git_commits": [],
                "working_tree_hints": [],
            }
        return by_day[date_key]

    for entry in journal_entries:
        heading = str(entry.get("heading", ""))
        date_key = date_key_from_timestampish(heading)
        if not date_key:
            continue
        bucket = ensure_day(date_key)
        bucket["journal_headings"].append(heading)
        items = list(entry.get("items", []))
        bucket["journal_items"].extend(items)
        bucket["feature_evolution"].extend(items[:4])

    for commit in git_commits:
        date_key = str(commit.get("date", "")).strip()
        if not date_key:
            continue
        bucket = ensure_day(date_key)
        bucket["git_commits"].append(commit)
        subject = clean_item(str(commit.get("subject", "")))
        if subject:
            bucket["feature_evolution"].append(subject)

    if not by_day:
        generated_date = date_key_from_timestampish(str(report["generated_at"]))
        fallback_date = generated_date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        bucket = ensure_day(fallback_date)
        bucket["working_tree_hints"].append(
            "no journal entries or git commits were available for daily summarization"
        )

    if report["git"]["working_tree"]["changes"]:
        generated_date = date_key_from_timestampish(str(report["generated_at"]))
        fallback_date = generated_date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        bucket = ensure_day(fallback_date)
        for change in report["git"]["working_tree"]["changes"][:8]:
            bucket["working_tree_hints"].append(f"{change['status']} {change['path']}")

    ordered_dates = sorted(by_day.keys(), reverse=True)
    daily_summaries: list[dict[str, object]] = []
    for date_key in ordered_dates:
        bucket = by_day[date_key]

        journal_items: list[str] = []
        seen_journal: set[str] = set()
        for item in bucket["journal_items"]:
            normalized = clean_item(str(item))
            if not normalized or normalized in seen_journal:
                continue
            seen_journal.add(normalized)
            journal_items.append(normalized)

        feature_evolution: list[str] = []
        seen_features: set[str] = set()
        for item in bucket["feature_evolution"]:
            normalized = clean_item(str(item))
            if not normalized or normalized in seen_features:
                continue
            seen_features.add(normalized)
            feature_evolution.append(normalized)

        daily_summaries.append(
            {
                "date": date_key,
                "journal_headings": list(bucket["journal_headings"])[: max(journal_limit, DEFAULT_DAILY_JOURNAL_HEADING_LIMIT)],
                "journal_items": journal_items[: max(journal_limit, DEFAULT_DAILY_JOURNAL_ITEM_LIMIT)],
                "feature_evolution": feature_evolution[: max(DEFAULT_DAILY_FEATURE_LIMIT, commit_limit)],
                "git_commits": list(bucket["git_commits"])[: max(commit_limit, DEFAULT_DAILY_COMMIT_LIMIT)],
                "working_tree_hints": list(bucket["working_tree_hints"])[:DEFAULT_WORKING_TREE_HINT_LIMIT],
            }
        )
    return daily_summaries


def build_report(project_root: Path, commit_limit: int, journal_limit: int) -> dict[str, object]:
    harness_root = project_root / ".aries_harness"
    if not harness_root.is_dir():
        raise FileNotFoundError(f"Missing harness directory: {harness_root}")

    history_root = harness_root / HISTORY_DIRNAME
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    identity = infer_identity(harness_root, project_root)

    state_sections = parse_sections(harness_root / "STATE.md")
    task_sections = parse_sections(harness_root / "TASK_STACK.md")
    mission_sections = parse_sections(harness_root / "MISSION.md")
    eval_sections = parse_sections(harness_root / "EVAL.md")
    memory_sections = parse_sections(harness_root / "MEMORY.md")
    journal_sections = parse_sections(harness_root / "JOURNAL.md")

    active_tasks = collect_bullets(task_sections.get("Active tasks", []))
    open_tasks = [item["text"] for item in active_tasks if item.get("checked") is not True]
    completed_tasks = [item["text"] for item in active_tasks if item.get("checked") is True]
    blockers = filter_placeholder_items(bullet_texts(task_sections.get("Blockers", [])))
    next_up = filter_placeholder_items(bullet_texts(task_sections.get("Next up", [])))
    milestone = nonempty_or_default(
        bullet_texts(task_sections.get("Current milestone", [])),
        "no current milestone recorded",
    )

    outcome = nonempty_or_default(
        bullet_texts(mission_sections.get("Outcome", [])),
        "no mission outcome recorded yet",
    )
    scope_boundary = filter_placeholder_items(bullet_texts(mission_sections.get("Scope boundary", [])))
    success_test = filter_placeholder_items(bullet_texts(mission_sections.get("Success test", [])))
    approval_boundaries = filter_placeholder_items(
        bullet_texts(mission_sections.get("Approval boundaries", []))
    )

    current_phase = first_or_default(
        bullet_texts(state_sections.get("Current phase", [])),
        "no current phase recorded",
    )
    workspace = nonempty_or_default(
        bullet_texts(state_sections.get("Working branch or workspace", [])),
        "no branch or workspace details recorded",
    )
    last_completed_step = nonempty_or_default(
        bullet_texts(state_sections.get("Last completed step", [])),
        "no completed step recorded",
    )
    last_verification = nonempty_or_default(
        bullet_texts(state_sections.get("Last verification", [])),
        "no verification recorded",
    )
    next_action = nonempty_or_default(
        bullet_texts(state_sections.get("Next action", [])),
        "no next action recorded",
    )

    verification_commands = filter_placeholder_items(
        bullet_texts(eval_sections.get("Verification commands", []))
    )
    acceptance_notes = filter_placeholder_items(
        bullet_texts(eval_sections.get("Acceptance notes", []))
    )
    durable_truths = filter_placeholder_items(
        bullet_texts(memory_sections.get("Active durable truths", []))
    )
    pending_promotions = filter_placeholder_items(
        bullet_texts(memory_sections.get("Pending promotions", []))
    )

    all_journal_entries = recent_journal_entries(journal_sections, len(journal_sections))
    journal_entries = all_journal_entries[:journal_limit]
    git_ready = git_available(project_root)
    branch = git_stdout(project_root, "rev-parse", "--abbrev-ref", "HEAD") if git_ready else ""
    head_subject = git_stdout(project_root, "log", "-1", "--pretty=%s") if git_ready else ""
    head_sha = git_stdout(project_root, "rev-parse", "--short", "HEAD") if git_ready else ""
    all_git_commits = all_commits(project_root) if git_ready else []
    recent_git_commits = all_git_commits[:commit_limit]
    tree = working_tree(project_root) if git_ready else {"clean": True, "change_count": 0, "changes": []}

    needs_attention: list[str] = []
    if blockers:
        needs_attention.extend(blockers)
    if not tree["clean"]:
        needs_attention.append(
            f"working tree is dirty with {tree['change_count']} tracked or untracked change(s)"
        )
    if pending_promotions:
        needs_attention.extend(f"pending promotion: {item}" for item in pending_promotions[:3])
    if not verification_commands and not acceptance_notes:
        needs_attention.append("verification gates are not documented yet in EVAL.md")
    if not next_up:
        needs_attention.append("no explicit next-up slice is recorded")

    roadmap_now = open_tasks[:6] if open_tasks else next_action[:3]
    roadmap_next = next_up[:6] if next_up else next_action[:3]
    roadmap_later = scope_boundary[:4] + success_test[:4]
    if not roadmap_later:
        roadmap_later = ["capture scope boundary and success test in MISSION.md"]

    recent_changes: list[str] = []
    for entry in journal_entries[:3]:
        for item in entry["items"][:3]:
            recent_changes.append(item)
    if not recent_changes:
        recent_changes.extend(completed_tasks[:3])
    recent_changes = recent_changes[:6]

    retrospective_wins = recent_changes[:4] if recent_changes else last_completed_step[:3]
    if not retrospective_wins:
        retrospective_wins = ["no recent completed work recorded"]

    evidence_sources = [
        ".aries_harness/MISSION.md",
        ".aries_harness/TASK_STACK.md",
        ".aries_harness/STATE.md",
        ".aries_harness/JOURNAL.md",
        ".aries_harness/EVAL.md",
        ".aries_harness/MEMORY.md",
    ]
    if git_ready:
        evidence_sources.extend(["git status --porcelain=v1", "git log"])

    doc_trace = build_doc_trace(project_root, harness_root, tree)
    evidence_sources.append(".aries_harness/**/*.md frontmatter + git file history")

    report = {
        "generated_at": timestamp,
        "project_root": str(project_root),
        "harness_root": str(harness_root),
        "history_root": str(history_root),
        "identity": identity,
        "commands": {
            "refresh": "/aries-harness history-refresh",
            "status": "/aries-harness history-status",
            "refresh_alias": "/ah history-refresh",
            "status_alias": "/ah history-status",
        },
        "state": {
            "current_phase": current_phase,
            "workspace": workspace,
            "last_completed_step": last_completed_step,
            "last_verification": last_verification,
            "next_action": next_action,
        },
        "task_stack": {
            "current_milestone": milestone,
            "active_tasks": active_tasks,
            "open_tasks": open_tasks,
            "completed_tasks": completed_tasks,
            "blockers": blockers if blockers else ["none recorded"],
            "next_up": roadmap_next,
        },
        "mission": {
            "outcome": outcome,
            "scope_boundary": scope_boundary,
            "success_test": success_test,
            "approval_boundaries": approval_boundaries,
        },
        "evaluation": {
            "verification_commands": verification_commands,
            "acceptance_notes": acceptance_notes,
        },
        "memory": {
            "durable_truths": durable_truths,
            "pending_promotions": pending_promotions,
        },
        "journal": {
            "recent_entries": journal_entries,
            "all_entries": all_journal_entries,
        },
        "git": {
            "available": git_ready,
            "branch": branch or "not a git repository",
            "head_sha": head_sha,
            "head_subject": head_subject,
            "recent_commits": recent_git_commits,
            "all_commits": all_git_commits,
            "working_tree": tree,
        },
        "roadmap": {
            "now": roadmap_now,
            "next": roadmap_next,
            "later": roadmap_later[:6],
        },
        "retrospective": {
            "recent_changes": recent_changes,
            "wins": retrospective_wins,
            "needs_attention": needs_attention[:6] if needs_attention else ["none highlighted"],
            "durable_reminders": durable_truths[:6] if durable_truths else ["no durable reminders recorded"],
        },
        "doc_trace": doc_trace,
        "evidence_sources": evidence_sources,
    }
    report["daily_summaries"] = build_daily_summaries(report, commit_limit, journal_limit)
    return report


def history_frontmatter(report: dict[str, object], role: str, generated_by: str) -> str:
    identity = report["identity"]
    lines = [
        "---",
        'schema_version: "0.1"',
        f'project_id: "{identity["project_id"]}"',
        f'owner: "{identity["owner"]}"',
        f'doc_role: "{role}"',
        f'harness_layer: "{SHARED_SUPPORT_SURFACE}"',
        f'managed_by: "{HARNESS_MANAGER}"',
        f'fingerprint: "{HISTORY_DOC_FINGERPRINT}"',
        f'generated_by: "{generated_by}"',
        f'initialized_at: "{identity["initialized_at"]}"',
        f'generated_at: "{report["generated_at"]}"',
        'effective_status: "generated"',
        f'effective_since: "{report["generated_at"]}"',
        "---",
        "",
    ]
    return "\n".join(lines)


def decorate_generated_history_markdown(
    content: str,
    report: dict[str, object],
    relative_path: str,
) -> str:
    frontmatter, body, _ = split_frontmatter_text(content)
    normalized = dict(frontmatter)
    normalized["content_fingerprint"] = content_fingerprint_for_body(body.lstrip("\n"))
    normalized.update(
        observed_git_trace(
            Path(report["project_root"]),
            f".aries_harness/{relative_path}",
        )
    )
    rendered = render_frontmatter(normalized) + body.lstrip("\n")
    if content.endswith("\n") and not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def render_history_readme(report: dict[str, object]) -> str:
    lines = [
        history_frontmatter(report, "history-readme", "/aries-harness history-refresh").rstrip(),
        "# Harness History Surface",
        "",
        f"Last refreshed: `{report['generated_at']}`",
        "",
        "This directory holds generated development-history views derived from harness facts and repo evidence.",
        "",
        "## Commands",
        "",
        "- `/aries-harness history-refresh` regenerates this history surface.",
        "- `/aries-harness history-status` prints a concise snapshot without rewriting files.",
        "- `/ah history-refresh` and `/ah history-status` are the short aliases.",
        "",
        "## Generated files",
        "",
        "- `STATUS.md` for current phase, milestone, verification, and next action.",
        "- `ROADMAP.md` for outcome, current milestone, now/next/later slices, and guardrails.",
        "- `TIMELINE.md` for journal milestones plus recent git commits.",
        "- `RETROSPECTIVE.md` for recent wins, attention areas, and durable reminders.",
        "- `DAILY_SUMMARY_INDEX.md` plus `daily/*.md` for per-day development memo and feature-evolution summaries.",
        "- `DOC_TRACE.md` for document governance, effective status, and recent revision trace.",
        "- `doc-trace.json` for machine-readable document trace details.",
        "- `summary.json` for machine-readable automation and inspection.",
        "",
        "## Evidence model",
        "",
    ]
    for source in report["evidence_sources"]:
        lines.append(f"- `{source}`")
    lines.extend(
        [
            "",
            "## Design rules",
            "",
            "- derive history from actual project evidence, not chat-only narrative",
            "- keep status, roadmap, timeline, and retrospective as separate views",
            "- promote durable lessons into `MEMORY.md`, `docs/insights.md`, or `AGENTS.md` instead of hiding them only in history output",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_daily_summary_index(report: dict[str, object]) -> str:
    lines = [
        history_frontmatter(report, "history-daily-summary-index", "/aries-harness history-refresh").rstrip(),
        "# Daily Summary Index",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "This index tracks the generated daily development summaries under `history/daily/`.",
        "",
        "## Daily reports",
        "",
    ]
    daily_summaries = report["daily_summaries"]
    if daily_summaries:
        for day in daily_summaries:
            lines.append(f"- `{day['date']}` -> `daily/{day['date']}.md`")
    else:
        lines.append("- no daily summaries were generated")
    lines.extend(
        [
            "",
            "## Design rule",
            "",
            "- daily summaries are generated projections of journal and git evidence, not manually maintained source truth",
            "- if the daily memo is weak, improve `JOURNAL.md`, `STATE.md`, `TASK_STACK.md`, or commit hygiene rather than editing generated files by hand",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_daily_summary_day(report: dict[str, object], day: dict[str, object]) -> str:
    lines = [
        history_frontmatter(report, "history-daily-summary", "/aries-harness history-refresh").rstrip(),
        f"# Daily Development Summary: {day['date']}",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Development memo",
        "",
    ]
    journal_headings = day["journal_headings"]
    journal_items = day["journal_items"]
    if journal_headings:
        for heading in journal_headings:
            lines.append(f"- journal entry: `{heading}`")
    if journal_items:
        for item in journal_items:
            lines.append(f"- {item}")
    if not journal_headings and not journal_items:
        lines.append("- no journal memo was captured for this day")

    lines.extend(
        [
            "",
            "## Feature evolution track",
            "",
        ]
    )
    if day["feature_evolution"]:
        for item in day["feature_evolution"]:
            lines.append(f"- {item}")
    else:
        lines.append("- no feature-evolution items were inferred for this day")

    lines.extend(
        [
            "",
            "## Git evidence",
            "",
        ]
    )
    if day["git_commits"]:
        for commit in day["git_commits"]:
            lines.append(f"- `{commit['sha']}` {commit['date']} {commit['subject']}")
    else:
        lines.append("- no git commits were captured for this day")

    if day["working_tree_hints"]:
        lines.extend(
            [
                "",
                "## Working tree hints",
                "",
            ]
        )
        for item in day["working_tree_hints"]:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Evidence sources",
            "",
            "- `JOURNAL.md`",
            "- `STATE.md`",
            "- `TASK_STACK.md`",
            "- `git log`",
            "- `git status --porcelain=v1` when relevant",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_status(report: dict[str, object]) -> str:
    git_state = report["git"]
    task_stack = report["task_stack"]
    state = report["state"]
    lines = [
        history_frontmatter(report, "history-status", "/aries-harness history-refresh").rstrip(),
        "# Current Status",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Current phase",
        "",
        f"- {state['current_phase']}",
        "",
        "## Branch and workspace",
        "",
    ]
    for item in state["workspace"]:
        lines.append(f"- {item}")
    if git_state["available"]:
        lines.append(f"- git branch: {git_state['branch']}")
        if git_state["head_sha"]:
            lines.append(f"- HEAD: `{git_state['head_sha']}` {git_state['head_subject']}")
        lines.append(
            f"- working tree: {'clean' if git_state['working_tree']['clean'] else 'dirty'}"
        )
        if not git_state["working_tree"]["clean"]:
            for change in git_state["working_tree"]["changes"][:8]:
                lines.append(f"- change: `{change['status']}` `{change['path']}`")
    else:
        lines.append("- git: unavailable")
    lines.extend(
        [
            "",
            "## Current milestone",
            "",
        ]
    )
    for item in task_stack["current_milestone"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Active tasks",
            "",
        ]
    )
    for item in task_stack["active_tasks"]:
        prefix = "[x]" if item["checked"] is True else "[ ]" if item["checked"] is False else "-"
        lines.append(f"- {prefix} {item['text']}")
    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )
    for item in task_stack["blockers"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Last verification",
            "",
        ]
    )
    last_verification = state["last_verification"]
    if last_verification and last_verification[0] != "no verification recorded":
        for item in last_verification:
            lines.append(f"- {item}")
    elif report["evaluation"]["verification_commands"]:
        for item in report["evaluation"]["verification_commands"]:
            lines.append(f"- verification command: {item}")
    else:
        lines.append("- no verification recorded")
    lines.extend(
        [
            "",
            "## Next action",
            "",
        ]
    )
    for item in state["next_action"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def render_roadmap(report: dict[str, object]) -> str:
    lines = [
        history_frontmatter(report, "history-roadmap", "/aries-harness history-refresh").rstrip(),
        "# Roadmap Snapshot",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Outcome target",
        "",
    ]
    for item in report["mission"]["outcome"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Current milestone",
            "",
        ]
    )
    for item in report["task_stack"]["current_milestone"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Now",
            "",
        ]
    )
    for item in report["roadmap"]["now"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Next",
            "",
        ]
    )
    for item in report["roadmap"]["next"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Later / guardrails",
            "",
        ]
    )
    for item in report["roadmap"]["later"]:
        lines.append(f"- {item}")
    if report["mission"]["approval_boundaries"]:
        lines.extend(
            [
                "",
                "## Approval boundaries",
                "",
            ]
        )
        for item in report["mission"]["approval_boundaries"]:
            lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def render_timeline(report: dict[str, object]) -> str:
    lines = [
        history_frontmatter(report, "history-timeline", "/aries-harness history-refresh").rstrip(),
        "# Timeline",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Journal milestones",
        "",
    ]
    journal_entries = report["journal"]["recent_entries"]
    if journal_entries:
        for entry in journal_entries:
            lines.append(f"### {entry['heading']}")
            lines.append("")
            for item in entry["items"]:
                lines.append(f"- {item}")
            lines.append("")
    else:
        lines.append("- no journal milestones recorded")
        lines.append("")
    lines.extend(
        [
            "## Recent git commits",
            "",
        ]
    )
    recent_commits = report["git"]["recent_commits"]
    if recent_commits:
        for commit in recent_commits:
            lines.append(f"- `{commit['sha']}` {commit['date']} {commit['subject']}")
    else:
        lines.append("- no git commit history available")
    lines.extend(
        [
            "",
            "## Working tree snapshot",
            "",
        ]
    )
    if report["git"]["working_tree"]["clean"]:
        lines.append("- working tree clean")
    else:
        for change in report["git"]["working_tree"]["changes"][:12]:
            lines.append(f"- `{change['status']}` `{change['path']}`")
    return "\n".join(lines).rstrip() + "\n"


def render_retrospective(report: dict[str, object]) -> str:
    lines = [
        history_frontmatter(report, "history-retrospective", "/aries-harness history-refresh").rstrip(),
        "# Retrospective Snapshot",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Recent changes",
        "",
    ]
    for item in report["retrospective"]["recent_changes"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## What is working",
            "",
        ]
    )
    for item in report["retrospective"]["wins"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## What needs attention",
            "",
        ]
    )
    for item in report["retrospective"]["needs_attention"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Durable reminders",
            "",
        ]
    )
    for item in report["retrospective"]["durable_reminders"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Promotion rule",
            "",
            "- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset",
            "- do not let retrospective output become the only place where important operating knowledge lives",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_doc_trace(report: dict[str, object]) -> str:
    trace = report["doc_trace"]
    summary = trace["summary"]
    lines = [
        history_frontmatter(report, "history-doc-trace", "/aries-harness history-refresh").rstrip(),
        "# Document Trace",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- managed Markdown docs: {summary['document_count']}",
        f"- docs with governance gaps: {summary['docs_with_issues']}",
        f"- dirty docs: {summary['dirty_docs']}",
        "",
        "## By layer",
        "",
    ]
    for layer_name in [META_DEFINE_LAYER, RUN_COOKING_LAYER, SHARED_SUPPORT_SURFACE, "unclassified"]:
        if layer_name in summary["by_layer"]:
            lines.append(f"- {layer_name}: {summary['by_layer'][layer_name]}")
    lines.extend(["", "## By effective status", ""])
    for status, count in sorted(summary["by_effective_status"].items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Managed docs", ""])

    for doc in trace["documents"]:
        lines.append(f"### {doc['path']}")
        lines.append("")
        lines.append(f"- role: {doc['doc_role']}")
        lines.append(f"- layer: {doc['layer'] or 'not set'}")
        lines.append(
            f"- effective status: {doc['effective_status']} since {doc['effective_since']}"
        )
        lines.append(f"- content fingerprint: `{doc['content_fingerprint'] or 'missing'}`")
        lines.append(
            "- trace: "
            f"{doc['trace_history_source'] or 'missing'} / "
            f"count={doc['trace_revision_count'] or 'missing'} / "
            f"sha={doc['trace_last_commit_sha'][:12] if doc['trace_last_commit_sha'] else 'none'}"
        )
        if doc["last_updated_at"]:
            lines.append(f"- last_updated_at: {doc['last_updated_at']}")
        if doc["completed_at"]:
            lines.append(f"- completed_at: {doc['completed_at']}")
        if doc["timebox_actual"]:
            lines.append(f"- timebox_actual: {doc['timebox_actual']}")
        if doc["latest_commit"] is not None:
            latest_commit = doc["latest_commit"]
            lines.append(
                f"- latest revision: `{latest_commit['sha']}` {latest_commit['date']} {latest_commit['subject']}"
            )
        else:
            lines.append("- latest revision: no git history recorded")
        lines.append(f"- dirty: {'yes' if doc['dirty'] else 'no'}")
        if doc["issues"]:
            lines.append("- governance issues:")
            for issue in doc["issues"]:
                lines.append(f"  - {issue}")
        recent_updates = doc["recent_updates"][1:] if doc["recent_updates"] else []
        if recent_updates:
            lines.append("- earlier revisions:")
            for update in recent_updates:
                lines.append(f"  - `{update['sha']}` {update['date']} {update['subject']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def summary_payload(report: dict[str, object]) -> dict[str, object]:
    return {
        "generated_at": report["generated_at"],
        "project_root": report["project_root"],
        "harness_root": report["harness_root"],
        "history_root": report["history_root"],
        "project_id": report["identity"]["project_id"],
        "owner": report["identity"]["owner"],
        "branch": report["git"]["branch"],
        "working_tree": report["git"]["working_tree"],
        "current_phase": report["state"]["current_phase"],
        "current_milestone": report["task_stack"]["current_milestone"],
        "next_action": report["state"]["next_action"],
        "roadmap": report["roadmap"],
        "retrospective": report["retrospective"],
        "daily_summaries": report["daily_summaries"],
        "doc_trace_summary": report["doc_trace"]["summary"],
        "evidence_sources": report["evidence_sources"],
    }


def text_status(report: dict[str, object], refreshed: bool) -> str:
    prefix = "Refreshed harness history" if refreshed else "Harness history status"
    lines = [
        f"{prefix}: {report['history_root']}",
        "",
        f"Current phase: {report['state']['current_phase']}",
        f"Current milestone: {report['task_stack']['current_milestone'][0]}",
        f"Branch: {report['git']['branch']}",
        f"Working tree: {'clean' if report['git']['working_tree']['clean'] else 'dirty'}",
        (
            "Doc governance: "
            f"{report['doc_trace']['summary']['document_count']} docs, "
            f"{report['doc_trace']['summary']['docs_with_issues']} with gaps"
        ),
        f"Next action: {report['state']['next_action'][0]}",
        "",
        "Roadmap now",
    ]
    for item in report["roadmap"]["now"][:5]:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append("Roadmap next")
    for item in report["roadmap"]["next"][:5]:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append("Recent commits")
    recent_commits = report["git"]["recent_commits"][:5]
    if recent_commits:
        for commit in recent_commits:
            lines.append(f"  - {commit['sha']} {commit['subject']}")
    else:
        lines.append("  - none")
    return "\n".join(lines)


def write_history_surface(project_root: Path, report: dict[str, object], dry_run: bool) -> None:
    harness_root = project_root / ".aries_harness"
    history_root = harness_root / HISTORY_DIRNAME
    daily_root = history_root / DAILY_SUMMARY_DIRNAME
    marker_payload, marker_needs_write = normalize_fingerprint(harness_root, project_root)

    files = {
        "README.md": render_history_readme(report),
        "STATUS.md": render_status(report),
        "ROADMAP.md": render_roadmap(report),
        "TIMELINE.md": render_timeline(report),
        "RETROSPECTIVE.md": render_retrospective(report),
        "DAILY_SUMMARY_INDEX.md": render_daily_summary_index(report),
        "DOC_TRACE.md": render_doc_trace(report),
        "doc-trace.json": json.dumps(report["doc_trace"], indent=2) + "\n",
        "summary.json": json.dumps(summary_payload(report), indent=2) + "\n",
    }
    markdown_files = {
        name: decorate_generated_history_markdown(content, report, f"history/{name}")
        for name, content in files.items()
        if name.endswith(".md")
    }
    files.update(markdown_files)

    if dry_run:
        print(f"Would refresh {history_root}")
        if marker_needs_write:
            print(f"  ensure {FINGERPRINT_FILE}")
        for filename in HISTORY_DOCS:
            print(f"  write {HISTORY_DIRNAME}/{filename}")
        for day in report["daily_summaries"]:
            print(f"  write {HISTORY_DIRNAME}/{DAILY_SUMMARY_DIRNAME}/{day['date']}.md")
        return

    history_root.mkdir(parents=True, exist_ok=True)
    daily_root.mkdir(parents=True, exist_ok=True)
    keep = history_root / ".gitkeep"
    keep.touch(exist_ok=True)
    (daily_root / ".gitkeep").touch(exist_ok=True)

    if marker_needs_write:
        marker_path = harness_root / FINGERPRINT_FILE
        marker_path.write_text(json.dumps(marker_payload, indent=2) + "\n", encoding="utf-8")

    for filename, content in files.items():
        (history_root / filename).write_text(content, encoding="utf-8")

    expected_daily_files: set[str] = set()
    for day in report["daily_summaries"]:
        daily_filename = f"{day['date']}.md"
        expected_daily_files.add(daily_filename)
        daily_content = render_daily_summary_day(report, day)
        daily_content = decorate_generated_history_markdown(
            daily_content,
            report,
            f"history/{DAILY_SUMMARY_DIRNAME}/{daily_filename}",
        )
        (daily_root / daily_filename).write_text(daily_content, encoding="utf-8")

    for existing in daily_root.glob("*.md"):
        if existing.name not in expected_daily_files:
            existing.unlink()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    try:
        report = build_report(project_root, max(1, args.commit_limit), max(1, args.journal_limit))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.subcommand == "refresh":
        write_history_surface(project_root, report, args.dry_run)
        if args.dry_run:
            return 0
        if args.json:
            print(json.dumps(summary_payload(report), indent=2))
        else:
            print(text_status(report, refreshed=True))
        return 0

    if args.json:
        print(json.dumps(summary_payload(report), indent=2))
    else:
        print(text_status(report, refreshed=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
