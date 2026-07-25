#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
import sys


HOT_MEMORY_MAX_LINES = 120
HOT_MEMORY_MAX_CHARS = 4000

# The minimum body sections a checkpoint must carry to be resumable by another
# agent, per the aries-harness-longrun "Minimum checkpoint contract". A checkpoint
# missing any of these is the most common silent longrun failure mode.
MINIMUM_CHECKPOINT_SECTIONS = [
    "objective",
    "completed work",
    "in-progress work",
    "next step",
    "blockers / risks",
    "verification performed",
    "verification still needed",
    "context state",
]

# An active checkpoint older than this is almost certainly abandoned (the
# longrun supervision cadence is 30 min; days-old "active" = no one is driving).
STALE_CHECKPOINT_DAYS = 2


@dataclass
class CardSummary:
    path: str
    memory_id: str
    kind: str
    status: str
    summary: str
    last_verified_at: str
    review_after: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect the Aries harness memory system under .aries_harness."
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
    return parser.parse_args()


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


def parse_iso_date(raw: str) -> date | None:
    if not raw:
        return None
    token = raw.strip().split("T", 1)[0]
    try:
        return date.fromisoformat(token)
    except ValueError:
        return None


def _normalize_heading(value: str) -> str:
    """Normalize a markdown heading so casing/slash-spacing cannot hide a match."""
    return value.lower().replace(" / ", "/").replace(" ", "")


def validate_checkpoint_contract(text: str) -> list[str]:
    """Return the minimum-contract sections missing from a checkpoint body.

    A checkpoint is only resumable when another agent can read objective,
    done/doing/next, risk, remaining verification, and context posture. This
    operationalizes the SKILL's "Recovery rule": if another agent cannot resume
    from the artifact, the checkpoint is incomplete.
    """
    heading_norms = {
        _normalize_heading(line.strip()[3:])
        for line in text.splitlines()
        if line.strip().startswith("## ")
    }
    return [sec for sec in MINIMUM_CHECKPOINT_SECTIONS if _normalize_heading(sec) not in heading_norms]


def extract_checkpoint_field(text: str, field: str) -> str:
    """Read a `- Field: value` line from a checkpoint (status, checkpoint time, ...)."""
    prefix = f"- {field}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return ""


def relative_to(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def collect_cards(cards_dir: Path, harness_root: Path) -> list[CardSummary]:
    cards: list[CardSummary] = []
    if not cards_dir.is_dir():
        return cards
    for path in sorted(cards_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        frontmatter = parse_frontmatter(path)
        cards.append(
            CardSummary(
                path=relative_to(path, harness_root),
                memory_id=frontmatter.get("memory_id", path.stem),
                kind=frontmatter.get("memory_kind", "unknown"),
                status=frontmatter.get("status", "unknown"),
                summary=frontmatter.get("summary", ""),
                last_verified_at=frontmatter.get("last_verified_at", ""),
                review_after=frontmatter.get("review_after", ""),
            )
        )
    return cards


def build_report(project_root: Path) -> dict[str, object]:
    harness_root = project_root / ".aries_harness"
    if not harness_root.is_dir():
        raise FileNotFoundError(f"Missing harness directory: {harness_root}")

    memory_file = harness_root / "MEMORY.md"
    memory_index = harness_root / "memory/INDEX.md"
    cards_dir = harness_root / "memory/cards"
    checkpoints_dir = harness_root / "checkpoints"
    runs_dir = harness_root / "runs"

    memory_text = memory_file.read_text(encoding="utf-8") if memory_file.is_file() else ""
    memory_lines = memory_text.splitlines()
    section_titles = [line[3:].strip() for line in memory_lines if line.startswith("## ")]
    cards = collect_cards(cards_dir, harness_root)

    cards_by_status: dict[str, int] = {}
    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_last_verified: list[str] = []
    review_due: list[str] = []
    today = date.today()

    for card in cards:
        cards_by_status[card.status] = cards_by_status.get(card.status, 0) + 1
        if card.memory_id in seen_ids:
            duplicate_ids.append(card.memory_id)
        else:
            seen_ids.add(card.memory_id)
        if card.status == "active" and not card.last_verified_at:
            missing_last_verified.append(card.memory_id)
        review_after = parse_iso_date(card.review_after)
        if review_after and review_after < today:
            review_due.append(card.memory_id)

    warnings: list[str] = []
    if memory_file.is_file():
        if len(memory_lines) > HOT_MEMORY_MAX_LINES:
            warnings.append(
                f"MEMORY.md exceeds the recommended hot-memory line budget ({len(memory_lines)} > {HOT_MEMORY_MAX_LINES})."
            )
        if len(memory_text) > HOT_MEMORY_MAX_CHARS:
            warnings.append(
                f"MEMORY.md exceeds the recommended hot-memory char budget ({len(memory_text)} > {HOT_MEMORY_MAX_CHARS})."
            )
        if "memory/INDEX.md" not in memory_text:
            warnings.append("MEMORY.md does not point to memory/INDEX.md for cold recall.")
    else:
        warnings.append("MEMORY.md is missing.")

    if not memory_index.is_file():
        warnings.append("memory/INDEX.md is missing.")
    if not cards_dir.is_dir():
        warnings.append("memory/cards/ directory is missing.")
    if duplicate_ids:
        warnings.append(f"Duplicate memory ids detected: {', '.join(duplicate_ids)}")
    if missing_last_verified:
        warnings.append(
            "Active cards missing last_verified_at: " + ", ".join(missing_last_verified)
        )
    if review_due:
        warnings.append("Cards past review_after: " + ", ".join(review_due))

    checkpoint_files = sorted(path.name for path in checkpoints_dir.glob("*.md")) if checkpoints_dir.is_dir() else []
    run_files = sorted(path.name for path in runs_dir.glob("*.md")) if runs_dir.is_dir() else []

    # Validate each checkpoint against the minimum resumability contract and
    # detect stale/abandoned active checkpoints. This operationalizes the
    # longrun "Recovery rule" and "Healthy longrun test" instead of leaving them
    # as prose-only guidance.
    checkpoints_detail: list[dict[str, object]] = []
    if checkpoints_dir.is_dir():
        for cp_path in sorted(checkpoints_dir.glob("*.md")):
            cp_text = cp_path.read_text(encoding="utf-8")
            status = extract_checkpoint_field(cp_text, "Status") or "unknown"
            time_raw = (
                extract_checkpoint_field(cp_text, "Checkpoint time")
                or extract_checkpoint_field(cp_text, "Last reviewed")
            )
            cp_date = parse_iso_date(time_raw)
            missing = validate_checkpoint_contract(cp_text)
            stale = (
                status.lower() == "active"
                and cp_date is not None
                and (today - cp_date).days > STALE_CHECKPOINT_DAYS
            )
            rel_cp = relative_to(cp_path, harness_root)
            checkpoints_detail.append(
                {
                    "path": rel_cp,
                    "status": status,
                    "checkpoint_time": time_raw,
                    "missing_sections": missing,
                    "stale": stale,
                }
            )
            if missing:
                warnings.append(
                    f"Checkpoint {rel_cp} missing contract sections: {', '.join(missing)}"
                )
            if stale:
                warnings.append(
                    f"Checkpoint {rel_cp} appears stale/abandoned "
                    f"(status active, last reviewed {time_raw})"
                )

    return {
        "project_root": str(project_root),
        "harness_root": str(harness_root),
        "hot_memory": {
            "path": relative_to(memory_file, harness_root),
            "present": memory_file.is_file(),
            "line_count": len(memory_lines),
            "char_count": len(memory_text),
            "recommended_max_lines": HOT_MEMORY_MAX_LINES,
            "recommended_max_chars": HOT_MEMORY_MAX_CHARS,
            "sections": section_titles,
        },
        "cold_memory": {
            "index_present": memory_index.is_file(),
            "cards_dir_present": cards_dir.is_dir(),
            "card_count": len(cards),
            "cards_by_status": cards_by_status,
            "cards": [asdict(card) for card in cards],
        },
        "episodic_memory": {
            "checkpoint_count": len(checkpoints_detail),
            "run_note_count": len(run_files),
            "checkpoints": checkpoints_detail,
            "checkpoint_contract": {
                "checked": True,
                "compliant": sum(1 for c in checkpoints_detail if not c["missing_sections"]),
                "total": len(checkpoints_detail),
            },
            "stale_checkpoints": [c["path"] for c in checkpoints_detail if c["stale"]],
        },
        "warnings": warnings,
    }


def render_text(report: dict[str, object]) -> str:
    hot_memory = report["hot_memory"]
    cold_memory = report["cold_memory"]
    episodic = report["episodic_memory"]
    warnings = report["warnings"]

    lines = [
        f"Harness memory inspection: {report['harness_root']}",
        "",
        "Hot memory",
        f"  - present: {hot_memory['present']}",
        f"  - size: {hot_memory['line_count']} lines / {hot_memory['char_count']} chars",
        f"  - budget: {hot_memory['recommended_max_lines']} lines / {hot_memory['recommended_max_chars']} chars",
        f"  - sections: {', '.join(hot_memory['sections']) if hot_memory['sections'] else 'none'}",
        "",
        "Cold recall",
        f"  - index present: {cold_memory['index_present']}",
        f"  - cards dir present: {cold_memory['cards_dir_present']}",
        f"  - card count: {cold_memory['card_count']}",
        f"  - by status: {cold_memory['cards_by_status'] if cold_memory['cards_by_status'] else '{}'}",
        "",
        "Episodic memory",
        f"  - checkpoints: {episodic['checkpoint_count']}",
        f"  - run notes: {episodic['run_note_count']}",
        "",
        "Warnings",
    ]
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
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
