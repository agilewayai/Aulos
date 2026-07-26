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

SECTION_FEATURES = "## 今天产品多了什么"
SECTION_STORIES = "## 谁因此更好用了"
SECTION_ARCHITECTURE = "## 系统怎么搭起来的"

SYSTEM_PROMPT = """你是 Aulos 产品编辑，把一天的开发证据写成普通人能读懂的中文博客。

硬性要求：
1. 只用简体中文。
2. 正文必须恰好包含这三个二级标题（顺序固定、措辞一字不差）：
   ## 今天产品多了什么
   ## 谁因此更好用了
   ## 系统怎么搭起来的
3. 从「产品特性 / 用户故事 / 产品架构」角度写，不要堆文件路径、命令、内部代号。
4. 首次不得不提到内部词时，用一句话解释它是干什么的。
5. 没有证据时如实说「这一天没有可确认的产品变化」，不要编造。
6. 开头用一行 `# 标题`，标题要像日报标题，不要写成「Git 日志」。
7. 每节 2–5 段短文即可，便于略读。
"""

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
            tok in lower for tok in ("/requests/", "/specs/", "/stories/", "req-", "spec-", "story-")
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
                # still include a short tail of recent journal
                text = text[-MAX_FILE_SNIPPET:]
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


def _journal_slice_for_day(text: str, day: str) -> str:
    """Keep headings/paragraphs that look related to the UTC day."""
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
        return "\n\n".join(chunks)[-MAX_FILE_SNIPPET:]
    return text[-MAX_FILE_SNIPPET:]


def render_fake_draft(evidence: DayEvidence) -> tuple[str, str]:
    title = f"# Aulos 开发日志 · {evidence.day}"
    commit_bits = [c.get("subject", "").strip() for c in evidence.commits if c.get("subject")]
    if commit_bits:
        feature_body = (
            "根据当天提交，产品侧大致推进了这些方向：\n\n"
            + "\n".join(f"- {s}" for s in commit_bits[:8])
            + "\n\n（这是离线草稿，配置真实 LLM 后可重新生成更顺的叙述。）"
        )
        story_body = (
            "这些改动主要让运维与听赏相关用户更省事："
            "例如配置集中到 Ops、听赏流程更稳、知识检索更准。"
            "若某条提交只是内部整理，对用户几乎无感，也会在此如实说明。"
        )
        arch_body = (
            "系统层面，当天工作落在网关、Ops 门户、技能包或知识面之间的衔接上。"
            "证据来自整仓 Git 与各子项目的 harness 日记，而不是口头转述。"
        )
    else:
        feature_body = "这一天没有可确认的产品代码提交。若 harness 日记有备忘，也尚未形成可对外讲的功能点。"
        story_body = "对用户而言，这一天没有可验证的体验变化。"
        arch_body = "架构故事空缺——等待有证据的一天再写。"

    body = "\n\n".join(
        [
            title,
            SECTION_FEATURES,
            feature_body,
            SECTION_STORIES,
            story_body,
            SECTION_ARCHITECTURE,
            arch_body,
        ]
    )
    return f"Aulos 开发日志 · {evidence.day}", body


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
        "day": row.day,
        "title": row.title,
        "provider": row.provider,
        "generated_at": to_utc_iso(row.generated_at),
        "evidence": evidence,
    }
    if include_body:
        out["body_md"] = row.body_md
    return out


def list_posts(db: Session) -> list[dict[str, Any]]:
    rows = db.query(DevBlogPost).order_by(DevBlogPost.day.desc()).all()
    return [post_to_dict(r, include_body=False) for r in rows]


def get_post(db: Session, day: str) -> DevBlogPost | None:
    day = validate_day(day)
    return db.query(DevBlogPost).filter(DevBlogPost.day == day).one_or_none()


async def generate_or_load(
    db: Session,
    day: str,
    *,
    force: bool = False,
    repo_root: Path | None = None,
) -> DevBlogPost:
    day = validate_day(day)
    existing = get_post(db, day)
    if existing is not None and not force:
        return existing

    evidence = collect_day_evidence(day, repo_root=repo_root)
    title, body, provider = await draft_body(db, evidence)
    payload = json.dumps(evidence.to_public(), ensure_ascii=False)

    if existing is None:
        row = DevBlogPost(
            day=day,
            title=title,
            body_md=body,
            evidence_json=payload,
            provider=provider,
            generated_at=utcnow(),
        )
        db.add(row)
    else:
        existing.title = title
        existing.body_md = body
        existing.evidence_json = payload
        existing.provider = provider
        existing.generated_at = utcnow()
        row = existing
    db.commit()
    db.refresh(row)
    return row
