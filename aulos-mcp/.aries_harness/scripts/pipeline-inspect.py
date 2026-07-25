#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
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

PIPELINE_PHASES = [
    {
        "id": "business_requirement",
        "heading": "1. Business requirement description",
        "directory": "references/requests",
        "readme": "references/requests/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "id": "domain_analysis",
        "heading": "2. Domain analysis and modeling",
        "directory": "references/domain",
        "readme": "references/domain/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "id": "system_design",
        "heading": "3. System design",
        "directory": "decisions/architecture",
        "readme": "decisions/architecture/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "id": "iteration_planning",
        "heading": "4. Iteration planning",
        "directory": "references/iterations",
        "readme": "references/iterations/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "id": "task_breakdown",
        "heading": "5. Task breakdown",
        "directory": "references/tasks",
        "readme": "references/tasks/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "id": "risk_tracking",
        "heading": "6. Risk tracking",
        "directory": "references/risks",
        "readme": "references/risks/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "id": "test_execution",
        "heading": "7. Test execution and fixes",
        "directory": "runs/tests",
        "readme": "runs/tests/README.md",
        "layer": RUN_COOKING_LAYER,
    },
    {
        "id": "iteration_report",
        "heading": "8. Iteration report",
        "directory": "runs/reports",
        "readme": "runs/reports/README.md",
        "layer": RUN_COOKING_LAYER,
    },
    {
        "id": "github_delivery",
        "heading": "9. GitHub delivery",
        "directory": "runs/github",
        "readme": "runs/github/README.md",
        "layer": RUN_COOKING_LAYER,
    },
    {
        "id": "production_deployment",
        "heading": "10. Production deployment",
        "directory": "runs/deployments",
        "readme": "runs/deployments/README.md",
        "layer": RUN_COOKING_LAYER,
    },
]

READY_STATUSES = {
    "ready",
    "done",
    "validated",
    "deployed",
    "complete",
    "completed",
}
PHASE_CLOSEOUT_TIMING_REQUIRED = {
    "iteration_planning",
    "task_breakdown",
    "risk_tracking",
    "test_execution",
    "iteration_report",
    "github_delivery",
}
PHASE_CLOSEOUT_TIMING_HEADING = "Closeout timing"
NOT_STARTED_STATUSES = {
    "",
    "not-started",
    "not started",
    "planned",
    "todo",
    "backlog",
}
PLACEHOLDER_VALUES = {
    "",
    "tbd",
    "todo",
    "none",
    "none yet",
    "not set",
    "pending",
}

SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
DATE_HEADING_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+\-Z]+)?$")
ISOISH_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+\-Z]+)?$")
EFFECTIVE_STATUSES = {"active", "generated", "archived", "superseded", "draft"}
TRACE_HISTORY_SOURCES = {"git", "filesystem-only"}
VOLATILE_TRACE_KEYS = {
    "content_fingerprint",
    "trace_history_source",
    "trace_last_commit_sha",
    "trace_last_commit_at",
    "trace_revision_count",
}

META_COLLECTION_READMES = {
    "references/requests/README.md",
    "references/specs/README.md",
    "references/stories/README.md",
    "references/domain/README.md",
    "references/iterations/README.md",
    "references/tasks/README.md",
    "references/risks/README.md",
    "decisions/architecture/README.md",
    "decisions/adrs/README.md",
}

RUN_COLLECTION_READMES = {
    "runs/tests/README.md",
    "runs/reports/README.md",
    "runs/github/README.md",
    "runs/deployments/README.md",
}

MANAGED_META_SUPPORT_COLLECTIONS = [
    {
        "directory": "references/specs",
        "readme": "references/specs/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "directory": "references/stories",
        "readme": "references/stories/README.md",
        "layer": META_DEFINE_LAYER,
    },
    {
        "directory": "decisions/adrs",
        "readme": "decisions/adrs/README.md",
        "layer": META_DEFINE_LAYER,
    },
]

GENERIC_META_COLLECTION_RULE = {
    "required_heading_groups": [
        {"label": "recommended naming", "options": ["Recommended naming"]},
        {"label": "artifact contract", "options": ["Each artifact should make clear"]},
        {"label": "layer rule", "options": ["Layer rule"]},
    ],
    "forbidden_heading_patterns": [
        (
            re.compile(r"\b(current milestone|active tasks|blockers|next up|current phase|last verification)\b", re.IGNORECASE),
            "looks like live run control; keep collection guides in `MetaDefineLayer` and move execution state to `RunCookingLayer` docs.",
        ),
        (
            re.compile(r"\b(test execution|iteration report|github delivery|production deployment|journal|timeline|retrospective)\b", re.IGNORECASE),
            "looks like execution evidence or history; collection guides should stay stable and route evidence elsewhere.",
        ),
    ],
}

GENERIC_RUN_COLLECTION_RULE = {
    "required_heading_groups": [
        {"label": "recommended naming", "options": ["Recommended naming"]},
        {"label": "artifact contract", "options": ["Each artifact should make clear"]},
        {"label": "layer rule", "options": ["Layer rule"]},
    ],
    "forbidden_heading_patterns": [
        (
            re.compile(r"\b(outcome|scope boundary|success test|approval boundaries|decision index|current decision)\b", re.IGNORECASE),
            "looks like stable mission or design truth; keep RunCooking collection guides out of `MetaDefineLayer` content.",
        ),
        (
            re.compile(r"\b(verification commands|acceptance notes|top-level risk contract|approval matrix|domain analysis|system design)\b", re.IGNORECASE),
            "looks like stable policy or design definition; keep collection guides focused on execution evidence shape.",
        ),
    ],
}

DOCUMENT_CONTENT_RULES = {
    "references/requests/README.md": {
        "required_heading_groups": [
            {"label": "semantic role", "options": ["Semantic role"]},
            {"label": "recommended naming", "options": ["Recommended naming"]},
            {"label": "belongs here", "options": ["Belongs here"]},
            {"label": "keep out", "options": ["Keep out"]},
            {"label": "trace links", "options": ["Trace links"]},
            {"label": "layer rule", "options": ["Layer rule"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(actors and behavior|quality and delivery constraints|slice overview|story detail template)\b", re.IGNORECASE),
                "looks like spec or story structure; keep request collection guidance at business-intent level.",
            ),
            (
                re.compile(r"\b(test execution|iteration report|github delivery|production deployment|current sprint|active tasks)\b", re.IGNORECASE),
                "looks like execution state or evidence; keep request collection guidance out of `RunCookingLayer` concerns.",
            ),
        ],
    },
    "references/specs/README.md": {
        "required_heading_groups": [
            {"label": "semantic role", "options": ["Semantic role"]},
            {"label": "recommended naming", "options": ["Recommended naming"]},
            {"label": "belongs here", "options": ["Belongs here"]},
            {"label": "keep out", "options": ["Keep out"]},
            {"label": "trace links", "options": ["Trace links"]},
            {"label": "layer rule", "options": ["Layer rule"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(problem|desired outcome|why now|request source)\b", re.IGNORECASE),
                "looks like request-brief structure; keep spec collection guidance at behavior and acceptance level.",
            ),
            (
                re.compile(r"\b(story detail template|current sprint|active tasks|test execution|iteration report|github delivery|production deployment)\b", re.IGNORECASE),
                "looks like story or run-evidence structure; keep spec collection guidance out of queue and evidence surfaces.",
            ),
        ],
    },
    "references/stories/README.md": {
        "required_heading_groups": [
            {"label": "semantic role", "options": ["Semantic role"]},
            {"label": "recommended naming", "options": ["Recommended naming"]},
            {"label": "belongs here", "options": ["Belongs here"]},
            {"label": "keep out", "options": ["Keep out"]},
            {"label": "trace links", "options": ["Trace links"]},
            {"label": "layer rule", "options": ["Layer rule"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(problem|desired outcome|why now|request source)\b", re.IGNORECASE),
                "looks like request-brief structure; keep story collection guidance focused on slices instead of upstream framing.",
            ),
            (
                re.compile(r"\b(actors and behavior|quality and delivery constraints|rollout or migration concerns)\b", re.IGNORECASE),
                "looks like spec-package structure; keep story collection guidance at slice and verification level.",
            ),
            (
                re.compile(r"\b(test execution|iteration report|github delivery|production deployment)\b", re.IGNORECASE),
                "looks like delivery evidence; keep story collection guidance out of `RunCookingLayer` evidence surfaces.",
            ),
        ],
    },
    "MISSION.md": {
        "required_heading_groups": [
            {"label": "outcome", "options": ["Outcome"]},
            {"label": "scope boundary", "options": ["Scope boundary"]},
            {"label": "success test", "options": ["Success test"]},
            {"label": "approval boundaries", "options": ["Approval boundaries"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(current milestone|active tasks|blockers|next up|current phase|last verification)\b", re.IGNORECASE),
                "looks like live execution state; keep `MISSION.md` stable and move run tracking into `RunCookingLayer` docs.",
            ),
            (
                re.compile(r"\b(iteration report|github delivery|production deployment|journal|timeline|retrospective|test execution)\b", re.IGNORECASE),
                "looks like execution evidence or history; keep `MISSION.md` at mission and scope only.",
            ),
        ],
    },
    "ADR.md": {
        "required_heading_groups": [
            {"label": "decision index", "options": ["Decision index"]},
            {"label": "current decision", "options": ["Current decision"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(current milestone|active tasks|blockers|next up|current phase|last verification)\b", re.IGNORECASE),
                "looks like live run control; keep `ADR.md` for architecture decisions only.",
            ),
            (
                re.compile(r"\b(iteration report|github delivery|production deployment|journal|timeline|retrospective)\b", re.IGNORECASE),
                "looks like delivery evidence or history; move it into `runs/` or `history/`.",
            ),
        ],
    },
    "RUNBOOK.md": {
        "required_heading_groups": [
            {"label": "start", "options": ["Start"]},
            {"label": "resume", "options": ["Resume"]},
            {"label": "human takeover", "options": ["Human takeover"]},
            {"label": "rollback", "options": ["Rollback"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(current milestone|active tasks|blockers|next up|current phase|last verification)\b", re.IGNORECASE),
                "looks like live execution state; keep `RUNBOOK.md` as a stable operator guide.",
            ),
            (
                re.compile(r"\b(decision index|current decision|timeline|retrospective)\b", re.IGNORECASE),
                "looks like architecture indexing or generated history; move it to the correct surface.",
            ),
        ],
    },
    "RISKS.md": {
        "required_heading_groups": [
            {"label": "risk contract", "options": ["Top-level risk contract", "High-risk actions"]},
            {"label": "approval matrix", "options": ["Approval matrix"]},
            {"label": "layer boundary", "options": ["Layer boundary"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(current|active|latest)\b.*\b(risk|run|state|phase|verification|report|deployment)\b", re.IGNORECASE),
                "looks like live risk tracking; move evolving detail into `references/risks/` or RunCooking evidence.",
            ),
            (
                re.compile(r"\b(test execution|test results|fix(?:es)?|iteration report|github delivery|production deployment|timeline|retrospective|journal)\b", re.IGNORECASE),
                "looks like execution evidence or history; keep root `RISKS.md` at top-level policy only.",
            ),
        ],
    },
    "EVAL.md": {
        "required_heading_groups": [
            {"label": "verification commands", "options": ["Verification commands"]},
            {"label": "acceptance notes", "options": ["Acceptance notes"]},
            {"label": "layer boundary", "options": ["Layer boundary"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(test run|test execution log|latest results?|fail(?:ed|ures?)|fix(?:es| attempts?)|incident|timeline|retrospective)\b", re.IGNORECASE),
                "looks like per-run test evidence; move it into `runs/tests/`.",
            ),
            (
                re.compile(r"\b(github delivery|production deployment|iteration report|journal|current phase|state)\b", re.IGNORECASE),
                "looks like RunCooking state or delivery evidence; keep `EVAL.md` as the verification contract only.",
            ),
        ],
    },
    "layers/MetaDefineLayer/README.md": {
        "required_heading_groups": [
            {"label": "owns root docs", "options": ["Owns root docs"]},
            {"label": "owns managed collections", "options": ["Owns managed collections"]},
            {"label": "rules", "options": ["Rules"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(current milestone|active tasks|current phase|last verification|journal|timeline)\b", re.IGNORECASE),
                "looks like run-state or history content; the layer manifest should only define layer ownership and rules.",
            ),
        ],
    },
    "TASK_STACK.md": {
        "required_heading_groups": [
            {"label": "current milestone", "options": ["Current milestone"]},
            {"label": "active tasks", "options": ["Active tasks"]},
            {"label": "blockers", "options": ["Blockers"]},
            {"label": "next up", "options": ["Next up"]},
            {"label": "layer boundary", "options": ["Layer boundary"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(architecture|system design|domain analysis|bounded context|adr|mission)\b", re.IGNORECASE),
                "looks like stable design or meta-definition content; move it into `MetaDefineLayer` docs or artifacts.",
            ),
            (
                re.compile(r"\b(verification commands|acceptance notes|approval matrix|top-level risk contract|risk register)\b", re.IGNORECASE),
                "looks like gate or policy definition; move it into `EVAL.md`, `RISKS.md`, or `references/risks/`.",
            ),
            (
                re.compile(r"\b(iteration report|github delivery|production deployment|retrospective|timeline)\b", re.IGNORECASE),
                "looks like closeout or delivery evidence; move it into `runs/` or `history/`.",
            ),
        ],
    },
    "PIPELINE.md": {
        "required_heading_groups": [
            {"label": "purpose", "options": ["Purpose"]},
            {"label": "current focus", "options": ["Current focus"]},
            {"label": "phase ledger", "options": ["Phase ledger"]},
            {"label": "pipeline rules", "options": ["Pipeline rules"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(outcome|scope boundary|success test|approval boundaries)\b", re.IGNORECASE),
                "looks like stable mission truth; keep `PIPELINE.md` focused on live phase progression.",
            ),
            (
                re.compile(r"\b(decision index|current decision|verification commands|acceptance notes|approval matrix|top-level risk contract)\b", re.IGNORECASE),
                "looks like stable meta-definition content; keep it in `MetaDefineLayer` docs.",
            ),
        ],
    },
    "STATE.md": {
        "required_heading_groups": [
            {"label": "current phase", "options": ["Current phase"]},
            {"label": "workspace", "options": ["Working branch or workspace"]},
            {"label": "last completed step", "options": ["Last completed step"]},
            {"label": "last verification", "options": ["Last verification"]},
            {"label": "next action", "options": ["Next action"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(outcome|scope boundary|success test|approval boundaries|decision index|current decision)\b", re.IGNORECASE),
                "looks like stable mission or architecture content; keep `STATE.md` for current execution state only.",
            ),
            (
                re.compile(r"\b(iteration report|github delivery|production deployment|retrospective|timeline)\b", re.IGNORECASE),
                "looks like closeout or generated history; move it into `runs/` or `history/`.",
            ),
        ],
    },
    "JOURNAL.md": {
        "require_any_sections": True,
        "allow_date_headings": True,
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(outcome|scope boundary|success test|approval boundaries|decision index|current decision)\b", re.IGNORECASE),
                "looks like stable mission or architecture truth; keep `JOURNAL.md` for episodic run notes only.",
            ),
            (
                re.compile(r"\b(verification commands|acceptance notes|approval matrix|current milestone|active tasks|blockers|next up)\b", re.IGNORECASE),
                "looks like policy or live queue definition; keep those in `EVAL.md`, `RISKS.md`, or `TASK_STACK.md`.",
            ),
        ],
    },
    "layers/RunCookingLayer/README.md": {
        "required_heading_groups": [
            {"label": "owns root docs", "options": ["Owns root docs"]},
            {"label": "owns managed collections", "options": ["Owns managed collections"]},
            {"label": "rules", "options": ["Rules"]},
        ],
        "forbidden_heading_patterns": [
            (
                re.compile(r"\b(outcome|scope boundary|success test|approval boundaries|decision index|current decision)\b", re.IGNORECASE),
                "looks like stable mission or design truth; the layer manifest should only define RunCooking ownership and rules.",
            ),
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect the Aries harness engineering pipeline under .aries_harness."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Target project root. Defaults to current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when warnings are present.",
    )
    return parser.parse_args()


def normalize_key(raw: str) -> str:
    token = raw.strip().lower()
    token = re.sub(r"[^a-z0-9]+", "_", token)
    return token.strip("_")


def clean_value(raw: str) -> str:
    token = raw.strip()
    if token.startswith("`") and token.endswith("`") and len(token) >= 2:
        token = token[1:-1]
    return token.strip()


def has_meaningful_value(value: str) -> bool:
    return value.strip().casefold() not in PLACEHOLDER_VALUES


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


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    body = text[4:]
    if "\n---\n" not in body:
        return text
    _, remainder = body.split("\n---\n", 1)
    return remainder


def content_fingerprint_for_body(body: str) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


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
    frontmatter, body, had_frontmatter = split_frontmatter_text(text)
    if not had_frontmatter:
        return text.rstrip("\n")
    identity_lines = [
        f"{key}={frontmatter[key]}"
        for key in sorted(frontmatter)
        if key not in VOLATILE_TRACE_KEYS
    ]
    return "\n".join(identity_lines + ["---", body.lstrip("\n").rstrip("\n")])


def observed_git_trace(project_root: Path, repo_relative_path: str) -> dict[str, str]:
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


def parse_sections(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    text = strip_frontmatter(path.read_text(encoding="utf-8"))
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for raw_line in text.splitlines():
        heading_match = SECTION_HEADING_RE.match(raw_line)
        if heading_match:
            current = {"heading": heading_match.group(1).strip(), "lines": []}
            sections.append(current)
            continue
        if current is not None:
            current["lines"].append(raw_line.rstrip())
    return sections


def audit_closeout_timing(
    phase_id: str,
    phase_heading: str,
    status: str,
    active_path: Path,
    harness_root: Path,
    warnings: list[str],
) -> dict[str, object] | None:
    if phase_id not in PHASE_CLOSEOUT_TIMING_REQUIRED:
        return None
    if status.strip().casefold() not in READY_STATUSES:
        return None
    if active_path.suffix.lower() != ".md" or not active_path.is_file():
        return None

    relative_path = relative_to(active_path, harness_root)
    frontmatter = parse_frontmatter(active_path)
    sections = parse_sections(active_path)
    headings = [str(section["heading"]) for section in sections]
    completed_at = frontmatter.get("completed_at", "").strip()
    timebox_actual = frontmatter.get("timebox_actual", "").strip()
    issues: list[str] = []

    if not completed_at:
        issues.append("missing completed_at")
    elif not ISOISH_DATE_RE.match(completed_at):
        issues.append("completed_at is not ISO-like")

    if not timebox_actual:
        issues.append("missing timebox_actual")
    elif "->" not in timebox_actual:
        issues.append("timebox_actual should use '<start> -> <end>' format")

    if PHASE_CLOSEOUT_TIMING_HEADING not in headings:
        issues.append("missing 'Closeout timing' section")

    for issue in issues:
        warnings.append(
            f"Closeout timing '{relative_path}' for phase '{phase_heading}' {issue}."
        )

    return {
        "path": relative_path,
        "completed_at": completed_at,
        "timebox_actual": timebox_actual,
        "has_closeout_timing_section": PHASE_CLOSEOUT_TIMING_HEADING in headings,
        "issue_count": len(issues),
        "issues": issues,
    }


def parse_pipeline_doc(path: Path) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    current_focus: dict[str, str] = {}
    phases: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return current_focus, phases

    text = path.read_text(encoding="utf-8")
    heading_map = {phase["heading"]: phase["id"] for phase in PIPELINE_PHASES}
    current_h2 = ""
    current_phase_id: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current_h2 = line[3:].strip()
            current_phase_id = None
            continue
        if line.startswith("### "):
            current_phase_id = heading_map.get(line[4:].strip())
            if current_phase_id is not None and current_phase_id not in phases:
                phases[current_phase_id] = {}
            continue
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        normalized_key = normalize_key(key)
        cleaned_value = clean_value(value)
        if current_h2 == "Current focus":
            current_focus[normalized_key] = cleaned_value
        elif current_phase_id is not None:
            phases[current_phase_id][normalized_key] = cleaned_value

    return current_focus, phases


def relative_to(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def expected_layer_for_relative_path(relative_path: str) -> str:
    if relative_path in ROOT_DOC_LAYERS:
        return ROOT_DOC_LAYERS[relative_path]
    for layer_name, manifest_path in LAYER_MANIFESTS.items():
        if relative_path == manifest_path:
            return layer_name
    if relative_path.startswith("layers/"):
        return SHARED_SUPPORT_SURFACE
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


def allowed_effective_statuses_for_relative_path(relative_path: str) -> set[str]:
    if relative_path == "INDEX.md" or relative_path.startswith("history/"):
        return {"generated"}
    if relative_path.startswith("archive/"):
        return {"archived", "superseded"}
    return {"active", "draft", "superseded"}


def content_rules_for_relative_path(relative_path: str) -> dict[str, object] | None:
    if relative_path in DOCUMENT_CONTENT_RULES:
        return DOCUMENT_CONTENT_RULES[relative_path]
    if relative_path in META_COLLECTION_READMES:
        return GENERIC_META_COLLECTION_RULE
    if relative_path in RUN_COLLECTION_READMES:
        return GENERIC_RUN_COLLECTION_RULE
    return None


def validate_layer_marker(
    path: Path,
    harness_root: Path,
    expected_layer: str,
    warnings: list[str],
    label: str,
) -> dict[str, object]:
    if not path.is_file():
        return {
            "relative_path": relative_to(path, harness_root),
            "present": False,
            "expected_layer": expected_layer,
            "declared_layer": "",
            "layer_matches": False,
        }

    frontmatter = parse_frontmatter(path)
    declared_layer = frontmatter.get("harness_layer", "")
    if declared_layer != expected_layer:
        actual = declared_layer or "missing"
        warnings.append(f"{label} should declare harness_layer '{expected_layer}' but found '{actual}'.")

    return {
        "relative_path": relative_to(path, harness_root),
        "present": True,
        "expected_layer": expected_layer,
        "declared_layer": declared_layer,
        "layer_matches": declared_layer == expected_layer,
    }


def audit_document_content(
    path: Path,
    harness_root: Path,
    warnings: list[str],
) -> dict[str, object] | None:
    if not path.is_file():
        return None
    relative_path = relative_to(path, harness_root)
    rules = content_rules_for_relative_path(relative_path)
    if rules is None:
        return None

    sections = parse_sections(path)
    headings = [str(section["heading"]) for section in sections]
    local_warnings: list[str] = []
    missing_required: list[dict[str, object]] = []
    forbidden_hits: list[dict[str, str]] = []

    if rules.get("require_any_sections") and not sections:
        local_warnings.append("has no level-2 sections, so content boundary review cannot run.")
    elif rules.get("required_heading_groups") and not sections:
        local_warnings.append("has no level-2 sections, so content boundary review cannot run.")

    for group in rules.get("required_heading_groups", []):
        if not any(option in headings for option in group["options"]):
            missing_required.append(group)
            options = ", ".join(group["options"])
            local_warnings.append(f"is missing the expected heading group '{group['label']}' ({options}).")

    for section in sections:
        heading = str(section["heading"])
        if DATE_HEADING_RE.match(heading) and not rules.get("allow_date_headings", False):
            message = "dated section headings look like run journaling and belong in `JOURNAL.md` or `runs/`."
            forbidden_hits.append({"heading": heading, "message": message})
            local_warnings.append(f"section '{heading}' {message}")
        for pattern, message in rules.get("forbidden_heading_patterns", []):
            if pattern.search(heading):
                forbidden_hits.append({"heading": heading, "message": message})
                local_warnings.append(f"section '{heading}' {message}")

    for issue in local_warnings:
        warnings.append(f"Content audit '{relative_path}' {issue}")

    return {
        "path": relative_path,
        "headings": headings,
        "missing_required": [
            {"label": group["label"], "options": group["options"]} for group in missing_required
        ],
        "forbidden_hits": forbidden_hits,
        "warning_count": len(local_warnings),
    }


def audit_document_governance(
    project_root: Path,
    harness_root: Path,
    warnings: list[str],
) -> dict[str, object]:
    docs: list[dict[str, object]] = []
    by_effective_status: dict[str, int] = {}

    for path in sorted(harness_root.rglob("*.md")):
        if not path.is_file():
            continue
        relative_path = relative_to(path, harness_root)
        repo_relative_path = f".aries_harness/{relative_path}"
        frontmatter = parse_frontmatter(path)
        observed_trace = observed_git_trace(project_root, repo_relative_path)
        observed_content_fingerprint = content_fingerprint_for_body(
            strip_frontmatter(path.read_text(encoding="utf-8")).lstrip("\n")
        )
        effective_status = frontmatter.get("effective_status", "")
        effective_since = frontmatter.get("effective_since", "")
        issues: list[str] = []

        if not frontmatter.get("managed_by"):
            issues.append("missing managed_by")
        if not frontmatter.get("fingerprint"):
            issues.append("missing fingerprint")
        if effective_status not in EFFECTIVE_STATUSES:
            issues.append("missing or invalid effective_status")
        else:
            allowed_statuses = allowed_effective_statuses_for_relative_path(relative_path)
            if effective_status not in allowed_statuses:
                issues.append(
                    "effective_status "
                    f"'{effective_status}' does not match the expected governance state for this path"
                )
        if not effective_since:
            issues.append("missing effective_since")
        elif not ISOISH_DATE_RE.match(effective_since):
            issues.append("effective_since is not ISO-like")
        if frontmatter.get("content_fingerprint", "") != observed_content_fingerprint:
            issues.append("content_fingerprint does not match current body")
        if frontmatter.get("trace_history_source", "") not in TRACE_HISTORY_SOURCES:
            issues.append("missing or invalid trace_history_source")
        elif effective_status != "generated" and frontmatter.get("trace_history_source", "") != observed_trace["trace_history_source"]:
            issues.append("trace_history_source does not match observed history source")
        if effective_status != "generated":
            if frontmatter.get("trace_last_commit_sha", "") != observed_trace["trace_last_commit_sha"]:
                issues.append("trace_last_commit_sha does not match observed latest commit")
            if frontmatter.get("trace_last_commit_at", "") != observed_trace["trace_last_commit_at"]:
                issues.append("trace_last_commit_at does not match observed latest commit date")
            if frontmatter.get("trace_revision_count", "") != observed_trace["trace_revision_count"]:
                issues.append("trace_revision_count does not match observed revision count")

        for issue in issues:
            warnings.append(f"Governance audit '{relative_path}' {issue}.")

        by_effective_status[effective_status or "missing"] = by_effective_status.get(
            effective_status or "missing",
            0,
        ) + 1
        docs.append(
            {
                "path": relative_path,
                "effective_status": effective_status,
                "effective_since": effective_since,
                "content_fingerprint": frontmatter.get("content_fingerprint", ""),
                "trace_history_source": frontmatter.get("trace_history_source", ""),
                "trace_last_commit_sha": frontmatter.get("trace_last_commit_sha", ""),
                "trace_last_commit_at": frontmatter.get("trace_last_commit_at", ""),
                "trace_revision_count": frontmatter.get("trace_revision_count", ""),
                "observed_content_fingerprint": observed_content_fingerprint,
                "observed_trace": observed_trace,
                "issue_count": len(issues),
                "issues": issues,
            }
        )

    return {
        "document_count": len(docs),
        "docs_with_issues": sum(1 for doc in docs if doc["issue_count"] > 0),
        "by_effective_status": by_effective_status,
        "documents": docs,
    }


def build_report(project_root: Path) -> dict[str, object]:
    harness_root = project_root / ".aries_harness"
    if not harness_root.is_dir():
        raise FileNotFoundError(f"Missing harness directory: {harness_root}")

    warnings: list[str] = []
    pipeline_path = harness_root / "PIPELINE.md"
    current_focus, parsed_phases = parse_pipeline_doc(pipeline_path)

    layer_manifests: list[dict[str, object]] = []
    content_audits: list[dict[str, object]] = []
    for layer_name, relative_path in LAYER_MANIFESTS.items():
        marker = validate_layer_marker(
            harness_root / relative_path,
            harness_root,
            layer_name,
            warnings,
            f"Layer manifest '{relative_path}'",
        )
        if marker["present"]:
            manifest_frontmatter = parse_frontmatter(harness_root / relative_path)
            declared_manifest_for = manifest_frontmatter.get("layer_manifest_for", "")
            if declared_manifest_for != layer_name:
                actual = declared_manifest_for or "missing"
                warnings.append(
                    f"Layer manifest '{relative_path}' should declare layer_manifest_for '{layer_name}' but found '{actual}'."
                )
            marker["layer_manifest_for"] = declared_manifest_for
        layer_manifests.append(marker)
        content_audit = audit_document_content(harness_root / relative_path, harness_root, warnings)
        if content_audit is not None:
            content_audits.append(content_audit)

    root_docs = []
    missing_root_docs = []
    for filename in CANONICAL_ROOT_DOCS:
        path = harness_root / filename
        expected_layer = ROOT_DOC_LAYERS[filename]
        marker = validate_layer_marker(path, harness_root, expected_layer, warnings, f"Root doc '{filename}'")
        root_docs.append({"name": filename, **marker})
        content_audit = audit_document_content(path, harness_root, warnings)
        if content_audit is not None:
            content_audits.append(content_audit)
        if not path.is_file():
            missing_root_docs.append(filename)
    if missing_root_docs:
        warnings.append("Missing canonical root docs: " + ", ".join(missing_root_docs))

    phases: list[dict[str, object]] = []
    for phase in PIPELINE_PHASES:
        directory = harness_root / phase["directory"]
        readme = harness_root / phase["readme"]
        entry = parsed_phases.get(phase["id"], {})
        status = entry.get("status", "")
        declared_directory = entry.get("canonical_directory", "")
        active_artifact = entry.get("active_artifact", "")
        verification = entry.get("verification_or_gate", "")
        latest_evidence = entry.get("latest_evidence", "")

        if phase["id"] not in parsed_phases:
            warnings.append(f"PIPELINE.md is missing phase heading: {phase['heading']}")
        else:
            for required_key in [
                "status",
                "canonical_directory",
                "active_artifact",
                "verification_or_gate",
                "latest_evidence",
            ]:
                if required_key not in entry:
                    warnings.append(
                        f"PIPELINE.md phase '{phase['heading']}' is missing field: {required_key}"
                    )

        if not directory.is_dir():
            warnings.append(f"Missing pipeline directory: {phase['directory']}/")
        if not readme.is_file():
            warnings.append(f"Missing pipeline README: {phase['readme']}")
        if declared_directory and declared_directory.rstrip("/") != phase["directory"]:
            warnings.append(
                f"PIPELINE.md phase '{phase['heading']}' points to '{declared_directory}' instead of '{phase['directory']}/'"
            )

        readme_marker = validate_layer_marker(
            readme,
            harness_root,
            phase["layer"],
            warnings,
            f"Pipeline README '{phase['readme']}'",
        )
        readme_content_audit = audit_document_content(readme, harness_root, warnings)
        if readme_content_audit is not None:
            content_audits.append(readme_content_audit)

        active_artifact_exists = False
        active_artifact_in_directory = False
        active_artifact_marker: dict[str, object] | None = None
        closeout_timing_audit: dict[str, object] | None = None
        if has_meaningful_value(active_artifact):
            active_path = harness_root / active_artifact
            active_artifact_exists = active_path.exists()
            active_artifact_in_directory = directory in active_path.parents if active_artifact_exists else False
            if not active_artifact_exists:
                warnings.append(
                    f"PIPELINE.md phase '{phase['heading']}' references a missing active artifact: {active_artifact}"
                )
            elif not active_artifact_in_directory:
                warnings.append(
                    f"PIPELINE.md phase '{phase['heading']}' active artifact is outside its canonical directory: {active_artifact}"
                )
            elif active_path.suffix.lower() == ".md":
                active_artifact_marker = validate_layer_marker(
                    active_path,
                    harness_root,
                    phase["layer"],
                    warnings,
                    f"Active artifact '{active_artifact}'",
                )
                closeout_timing_audit = audit_closeout_timing(
                    phase["id"],
                    phase["heading"],
                    status,
                    active_path,
                    harness_root,
                    warnings,
                )
        elif status.strip().casefold() not in NOT_STARTED_STATUSES:
            warnings.append(
                f"PIPELINE.md phase '{phase['heading']}' has status '{status or 'unknown'}' but no active artifact."
            )

        if status.strip().casefold() in READY_STATUSES and not has_meaningful_value(verification):
            warnings.append(
                f"PIPELINE.md phase '{phase['heading']}' has status '{status}' but no verification or gate."
            )

        phase_docs = []
        if directory.is_dir():
            for path in sorted(directory.glob("*.md")):
                if path.name == "README.md":
                    continue
                rel_path = relative_to(path, harness_root)
                marker = validate_layer_marker(
                    path,
                    harness_root,
                    phase["layer"],
                    warnings,
                    f"Phase doc '{rel_path}'",
                )
                phase_docs.append(marker)
        if not phase_docs and status.strip().casefold() not in NOT_STARTED_STATUSES:
            warnings.append(
                f"Pipeline directory '{phase['directory']}/' has no phase docs while status is '{status or 'unknown'}'."
            )

        phases.append(
            {
                "id": phase["id"],
                "heading": phase["heading"],
                "layer": phase["layer"],
                "directory": phase["directory"],
                "directory_present": directory.is_dir(),
                "readme": readme_marker,
                "status": status,
                "declared_directory": declared_directory,
                "active_artifact": active_artifact,
                "active_artifact_exists": active_artifact_exists,
                "active_artifact_in_directory": active_artifact_in_directory,
                "active_artifact_marker": active_artifact_marker,
                "closeout_timing_audit": closeout_timing_audit,
                "verification_or_gate": verification,
                "latest_evidence": latest_evidence,
                "phase_doc_count": len(phase_docs),
                "phase_docs": phase_docs,
            }
        )

    managed_meta_support_collections: list[dict[str, object]] = []
    for collection in MANAGED_META_SUPPORT_COLLECTIONS:
        directory = harness_root / collection["directory"]
        readme = harness_root / collection["readme"]

        if not directory.is_dir():
            warnings.append(f"Missing managed support collection: {collection['directory']}/")
        if not readme.is_file():
            warnings.append(f"Missing managed support README: {collection['readme']}")

        readme_marker = validate_layer_marker(
            readme,
            harness_root,
            collection["layer"],
            warnings,
            f"Managed support README '{collection['readme']}'",
        )
        readme_content_audit = audit_document_content(readme, harness_root, warnings)
        if readme_content_audit is not None:
            content_audits.append(readme_content_audit)

        doc_count = 0
        if directory.is_dir():
            doc_count = sum(1 for path in directory.glob("*.md") if path.name != "README.md")

        managed_meta_support_collections.append(
            {
                "directory": collection["directory"],
                "directory_present": directory.is_dir(),
                "readme": readme_marker,
                "doc_count": doc_count,
            }
        )

    allowed_stage_values = {phase["heading"].split(". ", 1)[1] for phase in PIPELINE_PHASES}
    current_stage = current_focus.get("current_stage", "")
    if current_stage and current_stage not in allowed_stage_values:
        warnings.append(f"PIPELINE.md current stage is not a recognized phase label: {current_stage}")

    governance_audit = audit_document_governance(project_root, harness_root, warnings)

    return {
        "project_root": str(project_root),
        "harness_root": str(harness_root),
        "pipeline_doc_present": pipeline_path.is_file(),
        "layer_manifests": layer_manifests,
        "current_focus": current_focus,
        "root_docs": root_docs,
        "content_audits": content_audits,
        "governance_audit": governance_audit,
        "phases": phases,
        "managed_meta_support_collections": managed_meta_support_collections,
        "warnings": warnings,
    }


def render_text(report: dict[str, object]) -> str:
    current_focus = report["current_focus"]
    phases = report["phases"]
    managed_meta_support_collections = report.get("managed_meta_support_collections", [])
    warnings = report["warnings"]
    layer_manifests = report["layer_manifests"]
    content_audits = report["content_audits"]
    governance_audit = report["governance_audit"]

    lines = [
        f"Harness engineering pipeline inspection: {report['harness_root']}",
        "",
        "Layer manifests",
    ]
    for manifest in layer_manifests:
        lines.append(
            f"  - {manifest['expected_layer']}: {'ok' if manifest['layer_matches'] else 'missing or mismatched'}"
        )
    lines.extend(
        [
            "",
            "Important document content audits",
        ]
    )
    for audit in content_audits:
        lines.append(
            f"  - {audit['path']}: {'ok' if audit['warning_count'] == 0 else str(audit['warning_count']) + ' issue(s)'}"
        )
    lines.extend(
        [
            "",
            "Document governance",
            f"  - managed docs: {governance_audit['document_count']}",
            f"  - docs with governance gaps: {governance_audit['docs_with_issues']}",
            "  - effective status counts: "
            + ", ".join(
                f"{status}={count}" for status, count in sorted(governance_audit["by_effective_status"].items())
            ),
        ]
    )
    lines.extend(
        [
            "",
            "Current focus",
            f"  - stage: {current_focus.get('current_stage', 'not set')}",
            f"  - active iteration: {current_focus.get('active_iteration', 'not set')}",
            f"  - latest status: {current_focus.get('latest_status', 'not set')}",
            f"  - next gate: {current_focus.get('next_gate', 'not set')}",
            "",
            "Phase ledger",
        ]
    )
    for phase in phases:
        lines.extend(
            [
                f"  - {phase['heading']}",
                f"    layer: {phase['layer']}",
                f"    status: {phase['status'] or 'not set'}",
                f"    directory: {phase['directory']} ({'ok' if phase['directory_present'] else 'missing'})",
                f"    readme layer: {'ok' if phase['readme']['layer_matches'] else 'missing or mismatched'}",
                f"    active artifact: {phase['active_artifact'] or 'not set'}",
                f"    verification or gate: {phase['verification_or_gate'] or 'not set'}",
                f"    phase docs: {phase['phase_doc_count']}",
            ]
        )
        closeout_timing_audit = phase.get("closeout_timing_audit")
        if closeout_timing_audit is not None:
            lines.append(
                "    closeout timing: "
                + ("ok" if closeout_timing_audit["issue_count"] == 0 else f"{closeout_timing_audit['issue_count']} issue(s)")
            )
            if closeout_timing_audit.get("completed_at"):
                lines.append(f"    completed_at: {closeout_timing_audit['completed_at']}")
            if closeout_timing_audit.get("timebox_actual"):
                lines.append(f"    timebox_actual: {closeout_timing_audit['timebox_actual']}")
    if managed_meta_support_collections:
        lines.extend(["", "Managed support collections"])
        for collection in managed_meta_support_collections:
            lines.extend(
                [
                    f"  - {collection['directory']}",
                    f"    directory: {'ok' if collection['directory_present'] else 'missing'}",
                    f"    readme layer: {'ok' if collection['readme']['layer_matches'] else 'missing or mismatched'}",
                    f"    docs: {collection['doc_count']}",
                ]
            )
    lines.extend(["", "Warnings"])
    if warnings:
        for warning in warnings:
            lines.append(f"  - {warning}")
    else:
        lines.append("  - none")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    try:
        report = build_report(project_root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))

    if args.strict and report["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
