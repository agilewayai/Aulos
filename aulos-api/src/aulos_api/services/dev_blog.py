"""Ops daily product development blog — evidence collect + LLM/fake draft (SPEC-009)."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import DevBlogPost, utcnow
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config

logger = logging.getLogger("aulos_api.dev_blog")

DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

from aulos_api.services.dev_blog_contract import (
    SECTION_ARCHITECTURE,
    SECTION_FEATURES,
    SECTION_STORIES,
    SYSTEM_PROMPT,
    validate_dev_blog_body,
)

MAX_COMMIT_LINES = 40
MAX_HARNESS_CHARS = 6000
MAX_FILE_SNIPPET = 1200


@dataclass
class DayEvidence:
    day: str
    commits: list[dict[str, str]] = field(default_factory=list)
    harness_excerpts: list[dict[str, str]] = field(default_factory=list)
    changed_harness_paths: list[str] = field(default_factory=list)
    repo_root: str = ""

    def to_public(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "repo_root": self.repo_root,
            "commit_count": len(self.commits),
            "commits": self.commits[:MAX_COMMIT_LINES],
            "harness_sources": [
                {"project": h.get("project", ""), "path": h.get("path", "")}
                for h in self.harness_excerpts
            ],
            "changed_harness_paths": self.changed_harness_paths[:80],
        }

    def prompt_blob(self) -> str:
        lines = [f"日期（UTC）: {self.day}", f"仓库根: {self.repo_root or '(unknown)'}", "", "## Git 提交"]
        if not self.commits:
            lines.append("（当日无提交）")
        else:
            for c in self.commits[:MAX_COMMIT_LINES]:
                lines.append(
                    f"- `{c.get('sha', '')}` {c.get('subject', '')} "
                    f"({c.get('author', '')} @ {c.get('date', '')})"
                )
        lines.append("")
        lines.append("## Harness 摘录")
        if not self.harness_excerpts:
            lines.append("（无 harness 摘录）")
        else:
            budget = MAX_HARNESS_CHARS
            for h in self.harness_excerpts:
                block = (
                    f"### {h.get('project', '')} — {h.get('path', '')}\n"
                    f"{h.get('text', '')[:MAX_FILE_SNIPPET]}\n"
                )
                if budget <= 0:
                    break
                take = block[:budget]
                lines.append(take)
                budget -= len(take)
        if self.changed_harness_paths:
            lines.append("")
            lines.append("## 当日变更的需求/规格/故事路径")
            for p in self.changed_harness_paths[:40]:
                lines.append(f"- {p}")
        return "\n".join(lines)


def validate_day(day: str) -> str:
    day = (day or "").strip()
    if not DAY_RE.match(day):
        raise ValueError("day must be YYYY-MM-DD (UTC calendar day)")
    return day


def resolve_repo_root(explicit: str | None = None) -> Path:
    raw = (explicit if explicit is not None else os.environ.get("AULOS_REPO_ROOT", "")).strip()
    if not raw:
        try:
            from aulos_api.config import get_settings

            raw = (get_settings().repo_root or "").strip()
        except Exception:
            raw = ""
    if raw:
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            return path
        raise FileNotFoundError(f"AULOS_REPO_ROOT is not a directory: {path}")

    # aulos_api/services/dev_blog.py → parents: services, aulos_api, src, aulos-api, monorepo
    here = Path(__file__).resolve()
    for parent in here.parents:
        siblings = list(parent.glob("aulos-*"))
        if len(siblings) >= 2 and (parent / "aulos-api").is_dir():
            return parent
    raise FileNotFoundError("Could not resolve monorepo root; set AULOS_REPO_ROOT")


def _run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        logger.warning("git_fail args=%s err=%s", args, (proc.stderr or "")[:300])
        return ""
    return proc.stdout or ""


def collect_day_evidence(day: str, *, repo_root: Path | None = None) -> DayEvidence:
    day = validate_day(day)
    root = repo_root or resolve_repo_root()
    evidence = DayEvidence(day=day, repo_root=str(root))

    since = f"{day}T00:00:00Z"
    until_dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
    until = until_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    log = _run_git(
        root,
        "log",
        f"--since={since}",
        f"--until={until}",
        "--date=iso-strict",
        "--pretty=format:%h%x09%ad%x09%an%x09%s",
    )
    for line in log.splitlines():
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        sha, date, author, subject = parts
        evidence.commits.append(
            {"sha": sha.strip(), "date": date.strip(), "author": author.strip(), "subject": subject.strip()}
        )

    name_status = _run_git(
        root,
        "log",
        f"--since={since}",
        f"--until={until}",
        "--name-only",
        "--pretty=format:",
    )
    changed: list[str] = []
    for line in name_status.splitlines():
        path = line.strip()
        if not path:
            continue
        lower = path.lower()
        if ".aries_harness/" in lower and any(
            tok in lower
            for tok in (
                "/requests/",
                "/specs/",
                "/stories/",
                "/runs/reviews/",
                "/decisions/",
                "req-",
                "spec-",
                "story-",
                "audit-",
                "adr-",
            )
        ):
            changed.append(path)
    # unique preserve order
    seen: set[str] = set()
    for p in changed:
        if p not in seen:
            seen.add(p)
            evidence.changed_harness_paths.append(p)

    for project_dir in sorted(root.glob("aulos-*")):
        if not project_dir.is_dir():
            continue
        harness = project_dir / ".aries_harness"
        if not harness.is_dir():
            continue
        candidates = [
            harness / "JOURNAL.md",
            harness / "history" / "daily" / f"{day}.md",
            harness / "STATE.md",
        ]
        for path in candidates:
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # Prefer journal entries that mention the day
            if path.name == "JOURNAL.md" and day not in text and f"T" not in text[:200]:
                text = _strip_frontmatter(text)[:MAX_FILE_SNIPPET]
            elif path.name == "JOURNAL.md":
                text = _journal_slice_for_day(text, day)
            evidence.harness_excerpts.append(
                {
                    "project": project_dir.name,
                    "path": str(path.relative_to(root)),
                    "text": text[:MAX_FILE_SNIPPET],
                }
            )

    return evidence


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def _journal_slice_for_day(text: str, day: str) -> str:
    """Keep headings/paragraphs that look related to the UTC day (newest-first in JOURNAL)."""
    chunks: list[str] = []
    current: list[str] = []
    keep = False
    for line in text.splitlines():
        if line.startswith("## "):
            if keep and current:
                chunks.append("\n".join(current))
            current = [line]
            keep = day in line
        else:
            current.append(line)
            if day in line:
                keep = True
    if keep and current:
        chunks.append("\n".join(current))
    if chunks:
        # JOURNAL is reverse-chronological — keep the start of the joined slice (newest entries).
        return "\n\n".join(chunks)[:MAX_FILE_SNIPPET]
    # No dated headings matched: take the top of the file (recent entries), skip YAML frontmatter.
    return _strip_frontmatter(text)[:MAX_FILE_SNIPPET]


def render_fake_draft(evidence: DayEvidence) -> tuple[str, str]:
    title = f"Aulos 开发轨迹 · {evidence.day}"
    commit_bits = [c.get("subject", "").strip() for c in evidence.commits if c.get("subject")]
    harness_projects = sorted({h.get("project", "") for h in evidence.harness_excerpts if h.get("project")})

    if commit_bits or harness_projects:
        feature_lines = [f"- Git：{s}" for s in commit_bits[:8]]
        if harness_projects:
            feature_lines.append(f"- Harness 涉及子项目：{', '.join(harness_projects)}")
        if evidence.changed_harness_paths:
            feature_lines.append(
                f"- 当日变更 REQ/SPEC/故事 {len(evidence.changed_harness_paths)} 处（见 evidence）"
            )
        feature_body = "当日可核对变更：\n\n" + "\n".join(feature_lines)
        story_body = (
            "影响范围需结合上表判断：若仅为测试、Harness 整理或内部重构，"
            "则终端用户无可见变化；若涉及门户、导赏、鉴权或 Ops 配置，则对应角色可见。"
        )
        arch_body = (
            "证据来源为整仓 Git log 与各子项目 Harness JOURNAL / history daily。"
            "具体模块边界以提交说明与 SPEC 为准；离线 fake 草稿不做推断。"
        )
    else:
        feature_body = "当日无可确认的 Git 提交或 Harness 摘录。"
        story_body = "无终端用户可见变化。"
        arch_body = "无架构层变更记录。"

    body = "\n\n".join(
        [
            f"# {title}",
            SECTION_FEATURES,
            feature_body,
            SECTION_STORIES,
            story_body,
            SECTION_ARCHITECTURE,
            arch_body,
        ]
    )
    return title, body


def parse_title_from_markdown(body: str, day: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()[:255]
    return f"Aulos 开发日志 · {day}"


def ensure_sections(body: str) -> str:
    """If the model drifts, append missing required headings with a short note."""
    missing = [h for h in (SECTION_FEATURES, SECTION_STORIES, SECTION_ARCHITECTURE) if h not in body]
    if not missing:
        return body
    parts = [body.rstrip(), ""]
    for h in missing:
        parts.append(h)
        parts.append("（模型未输出本节，请强制重新生成。）")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


async def draft_body(db: Session, evidence: DayEvidence) -> tuple[str, str, str]:
    """Return (title, body_md, provider)."""
    cfg = load_llm_config(db)
    live = await chat_with_ops_llm(
        db=db,
        message=evidence.prompt_blob(),
        system_prompt=SYSTEM_PROMPT,
        timeout=90.0,
    )
    if live is None:
        title, body = render_fake_draft(evidence)
        return title, body, "fake"
    reply, provider = live
    body = ensure_sections(reply.strip())
    warnings = validate_dev_blog_body(body)
    if warnings:
        logger.warning("dev_blog_contract_warnings day=%s %s", evidence.day, "; ".join(warnings))
    title = parse_title_from_markdown(body, evidence.day)
    return title, body, provider or cfg.active_provider


def post_to_dict(row: DevBlogPost, *, include_body: bool = True) -> dict[str, Any]:
    from aulos_api.timefmt import to_utc_iso

    evidence: dict[str, Any]
    try:
        evidence = json.loads(row.evidence_json or "{}")
    except json.JSONDecodeError:
        evidence = {}
    out: dict[str, Any] = {
        "id": row.id,
        "day": row.day,
        "title": row.title,
        "provider": row.provider,
        "generated_at": to_utc_iso(row.generated_at),
        "evidence": evidence,
    }
    if include_body:
        out["body_md"] = row.body_md
    return out


def list_posts(
    db: Session,
    *,
    day: str | None = None,
    day_from: str | None = None,
    day_to: str | None = None,
    q: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = db.query(DevBlogPost)
    if day:
        day = validate_day(day)
        query = query.filter(DevBlogPost.day == day)
    if day_from:
        day_from = validate_day(day_from)
        query = query.filter(DevBlogPost.day >= day_from)
    if day_to:
        day_to = validate_day(day_to)
        query = query.filter(DevBlogPost.day <= day_to)
    needle = (q or "").strip()
    if needle:
        like = f"%{needle}%"
        query = query.filter(
            (DevBlogPost.title.ilike(like)) | (DevBlogPost.body_md.ilike(like))
        )
    rows = (
        query.order_by(DevBlogPost.generated_at.desc(), DevBlogPost.id.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [post_to_dict(r, include_body=False) for r in rows]


def get_post_by_id(db: Session, post_id: int) -> DevBlogPost | None:
    if post_id < 1:
        return None
    return db.query(DevBlogPost).filter(DevBlogPost.id == post_id).one_or_none()


def get_latest_post_for_day(db: Session, day: str) -> DevBlogPost | None:
    day = validate_day(day)
    return (
        db.query(DevBlogPost)
        .filter(DevBlogPost.day == day)
        .order_by(DevBlogPost.generated_at.desc(), DevBlogPost.id.desc())
        .first()
    )


async def generate_post(
    db: Session,
    day: str,
    *,
    post_id: int | None = None,
    repo_root: Path | None = None,
) -> DevBlogPost:
    """Create a new post, or rewrite an existing one when post_id is set."""
    day = validate_day(day)
    evidence = collect_day_evidence(day, repo_root=repo_root)
    title, body, provider = await draft_body(db, evidence)
    payload = json.dumps(evidence.to_public(), ensure_ascii=False)
    now = utcnow()

    if post_id is not None:
        existing = get_post_by_id(db, post_id)
        if existing is None:
            raise ValueError(f"post_id {post_id} not found")
        existing.day = day
        existing.title = title
        existing.body_md = body
        existing.evidence_json = payload
        existing.provider = provider
        existing.generated_at = now
        row = existing
    else:
        row = DevBlogPost(
            day=day,
            title=title,
            body_md=body,
            evidence_json=payload,
            provider=provider,
            generated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


# Back-compat aliases
def get_post(db: Session, day: str) -> DevBlogPost | None:
    return get_latest_post_for_day(db, day)


async def generate_or_load(
    db: Session,
    day: str,
    *,
    force: bool = False,
    post_id: int | None = None,
    repo_root: Path | None = None,
) -> DevBlogPost:
    """Legacy entry: force+post_id rewrites; otherwise always creates a new post."""
    if force and post_id is not None:
        return await generate_post(db, day, post_id=post_id, repo_root=repo_root)
    if force and post_id is None:
        existing = get_latest_post_for_day(db, day)
        if existing is not None:
            return await generate_post(db, day, post_id=existing.id, repo_root=repo_root)
    return await generate_post(db, day, repo_root=repo_root)
