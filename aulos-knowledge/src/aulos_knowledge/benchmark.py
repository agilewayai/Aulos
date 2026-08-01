"""Knowledge plane benchmark (KB-BENCH-001)."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import func
from sqlalchemy.orm import Session

from aulos_knowledge.connectors import connector_registered
from aulos_knowledge.db import (
    BenchmarkRun,
    FetchJob,
    KnowledgeDocument,
    SourceAuthority,
    WorkEntity,
    utcnow,
)
from aulos_knowledge.registry import default_manifest_path, load_registry_manifest
from aulos_knowledge.retrieve import retrieve

logger = logging.getLogger("aulos_knowledge.benchmark")

DIMENSION_WEIGHTS = {
    "corpus": 0.20,
    "registry": 0.15,
    "provenance": 0.15,
    "retrieval": 0.40,
    "pipeline": 0.10,
}

DIMENSION_LABELS = {
    "corpus": "Corpus coverage",
    "registry": "Registry health",
    "provenance": "Provenance integrity",
    "retrieval": "Retrieval accuracy",
    "pipeline": "Pipeline health",
}


def default_suite_path() -> Path:
    here = Path(__file__).resolve()
    root = here.parents[2]  # aulos-knowledge/
    return root / "data" / "benchmark" / "suite.yaml"


def load_benchmark_suite(path: Path | None = None) -> dict[str, Any]:
    p = path or default_suite_path()
    if not p.is_file():
        return {"revision": "", "cases": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"benchmark suite must be a mapping: {p}")
    return data


def _clamp(score: float) -> float:
    return max(0.0, min(100.0, round(score, 2)))


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _score_corpus(db: Session) -> dict[str, Any]:
    docs = db.query(KnowledgeDocument).count()
    published = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == "published").count()
    quarantine = docs - published
    works_total = db.query(WorkEntity).count()
    works_covered = (
        db.query(func.count(func.distinct(KnowledgeDocument.aulos_work_id)))
        .filter(KnowledgeDocument.status == "published", KnowledgeDocument.aulos_work_id != "")
        .scalar()
        or 0
    )
    publish_ratio = (published / docs) if docs else 0.0
    work_coverage = (works_covered / works_total) if works_total else 0.0
    # Favor published corpus + work linkage
    score = _clamp(publish_ratio * 55 + work_coverage * 45)
    return {
        "score": score,
        "documents": docs,
        "published": published,
        "quarantine": quarantine,
        "publish_ratio": round(publish_ratio, 4),
        "works_total": works_total,
        "works_with_published_docs": works_covered,
        "work_coverage_ratio": round(work_coverage, 4),
    }


def _score_registry(db: Session) -> dict[str, Any]:
    sources = db.query(SourceAuthority).all()
    total = len(sources)
    verified = sum(1 for s in sources if (s.verification_status or "") == "verified")
    enabled = sum(1 for s in sources if s.enabled)
    crawl_ready = sum(
        1
        for s in sources
        if (s.verification_status or "") == "verified"
        and s.enabled
        and connector_registered(s.connector or "")
    )
    manifest = load_registry_manifest(default_manifest_path())
    revision = str(manifest.get("revision") or "")
    verified_ratio = verified / total if total else 0.0
    crawl_ratio = crawl_ready / total if total else 0.0
    score = _clamp(verified_ratio * 50 + crawl_ratio * 50)
    return {
        "score": score,
        "sources_total": total,
        "sources_verified": verified,
        "sources_enabled": enabled,
        "sources_crawl_ready": crawl_ready,
        "registry_revision": revision,
        "verified_ratio": round(verified_ratio, 4),
        "crawl_ready_ratio": round(crawl_ratio, 4),
    }


def _score_provenance(db: Session) -> dict[str, Any]:
    published_docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == "published").all()
    if not published_docs:
        return {
            "score": 0.0,
            "published_docs": 0,
            "complete_provenance": 0,
            "complete_ratio": 0.0,
        }
    complete = 0
    for d in published_docs:
        if d.source_id and d.artifact_id and d.job_id and d.extractor_version:
            complete += 1
    ratio = complete / len(published_docs)
    return {
        "score": _clamp(ratio * 100),
        "published_docs": len(published_docs),
        "complete_provenance": complete,
        "complete_ratio": round(ratio, 4),
    }


def _score_pipeline(db: Session) -> dict[str, Any]:
    jobs = db.query(FetchJob).order_by(FetchJob.id.desc()).limit(40).all()
    if not jobs:
        return {"score": 50.0, "sample_size": 0, "succeeded": 0, "failed": 0, "success_ratio": None}
    succeeded = sum(1 for j in jobs if j.status == "succeeded")
    failed = sum(1 for j in jobs if j.status == "failed")
    denom = succeeded + failed
    ratio = succeeded / denom if denom else 1.0
    return {
        "score": _clamp(ratio * 100),
        "sample_size": len(jobs),
        "succeeded": succeeded,
        "failed": failed,
        "success_ratio": round(ratio, 4) if denom else None,
    }


def _eval_retrieval_case(db: Session, case: dict[str, Any]) -> dict[str, Any]:
    cid = str(case.get("id") or "")
    optional = bool(case.get("optional"))
    result = retrieve(
        db,
        query=str(case.get("query") or ""),
        work_id=str(case.get("work_id") or ""),
        composer_id=str(case.get("composer_id") or ""),
        k=6,
    )
    hits = result.get("hits") or []
    top_score = float(hits[0]["score"]) if hits else 0.0
    notes: list[str] = []
    passed = True

    min_hits = int(case.get("min_hits") or 0)
    if len(hits) < min_hits:
        passed = False
        notes.append(f"hits {len(hits)} < min {min_hits}")

    min_top = float(case.get("min_top_score") or 0.0)
    if top_score < min_top:
        passed = False
        notes.append(f"top_score {top_score} < min {min_top}")

    if case.get("require_work_id_match") and case.get("work_id"):
        want = str(case["work_id"])
        for h in hits:
            if (h.get("aulos_work_id") or "") != want:
                passed = False
                notes.append(f"work_id mismatch: got {h.get('aulos_work_id')}")
                break

    for token in list(case.get("forbid_title_tokens") or []):
        tok = str(token).lower()
        for h in hits:
            title = str(h.get("title") or "").lower()
            if tok in title:
                passed = False
                notes.append(f"forbidden token '{token}' in hit title")
                break

    if optional and not hits:
        passed = True
        notes.append("optional case — no hits OK")

    case_score = 100.0 if passed else 0.0
    return {
        "id": cid,
        "label": str(case.get("label") or cid),
        "passed": passed,
        "optional": optional,
        "hits": len(hits),
        "top_score": top_score,
        "case_score": case_score,
        "notes": notes,
        "hits_preview": [
            {
                "title": h.get("title"),
                "score": h.get("score"),
                "aulos_work_id": h.get("aulos_work_id"),
                "source_id": h.get("source_id"),
            }
            for h in hits[:3]
        ],
    }


def _score_retrieval(db: Session, suite: dict[str, Any]) -> dict[str, Any]:
    cases = [c for c in list(suite.get("cases") or []) if isinstance(c, dict)]
    results = [_eval_retrieval_case(db, c) for c in cases]
    required = [r for r in results if not r.get("optional")]
    if not required:
        return {"score": 0.0, "cases": results, "passed": 0, "total": 0, "pass_ratio": 0.0}
    passed = sum(1 for r in required if r.get("passed"))
    ratio = passed / len(required)
    return {
        "score": _clamp(ratio * 100),
        "cases": results,
        "passed": passed,
        "total": len(required),
        "pass_ratio": round(ratio, 4),
    }


def _overall_score(dimensions: dict[str, dict[str, Any]]) -> float:
    total = 0.0
    for key, weight in DIMENSION_WEIGHTS.items():
        total += float(dimensions[key]["score"]) * weight
    return _clamp(total)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Knowledge benchmark report — run #{report['id']}",
        "",
        f"- **When:** {report['created_at']}",
        f"- **Overall:** {report['overall_score']} ({report['grade']})",
        f"- **Duration:** {report['duration_ms']} ms",
        f"- **Registry:** {report.get('registry_revision') or '—'}",
        f"- **Suite:** {report.get('suite_revision') or '—'}",
        "",
        "## Dimensions",
        "",
        "| Dimension | Score | Weight |",
        "| --- | ---: | ---: |",
    ]
    for dim, weight in DIMENSION_WEIGHTS.items():
        lines.append(f"| {dim} | {report['dimensions'][dim]['score']} | {int(weight * 100)}% |")
    lines.extend(["", "## Retrieval cases", ""])
    for c in report["dimensions"]["retrieval"].get("cases") or []:
        mark = "PASS" if c.get("passed") else "FAIL"
        opt = " (optional)" if c.get("optional") else ""
        lines.append(f"- **{mark}** `{c.get('id')}` — {c.get('label')}{opt} · hits={c.get('hits')} top={c.get('top_score')}")
        for n in c.get("notes") or []:
            lines.append(f"  - {n}")
    lines.append("")
    return "\n".join(lines)


def run_benchmark(db: Session, *, trigger: str = "ops", sync: bool | None = None) -> dict[str, Any]:
    """Enqueue benchmark; run inline when sync_jobs (dev/tests) else background thread."""
    from aulos_knowledge.benchmark_queue import enqueue_and_maybe_run as enqueue_benchmark_run

    row = enqueue_benchmark_run(db, trigger=trigger, sync=sync)
    if row.status in ("succeeded", "failed"):
        report = get_benchmark_run(db, row.id)
        if report:
            return report
    return benchmark_run_summary(row)


def execute_benchmark_run(db: Session, run_id: int) -> dict[str, Any]:
    """State machine: queued|running → succeeded|failed. Performs scoring work."""
    row = db.get(BenchmarkRun, run_id)
    if row is None:
        raise ValueError(f"benchmark run not found: {run_id}")
    if row.status == "succeeded":
        existing = get_benchmark_run(db, run_id)
        if existing:
            return existing
    if row.status == "failed":
        raise RuntimeError(row.error or f"benchmark run {run_id} failed")

    row.status = "running"
    row.started_at = utcnow()
    row.error = ""
    db.commit()

    t0 = time.perf_counter()
    try:
        suite = load_benchmark_suite()
        dimensions = {
            "corpus": _score_corpus(db),
            "registry": _score_registry(db),
            "provenance": _score_provenance(db),
            "retrieval": _score_retrieval(db, suite),
            "pipeline": _score_pipeline(db),
        }
        overall = _overall_score(dimensions)
        duration_ms = int((time.perf_counter() - t0) * 1000)
        report: dict[str, Any] = {
            "id": row.id,
            "status": "succeeded",
            "trigger": row.trigger,
            "created_at": row.created_at.isoformat() if row.created_at else datetime.now(timezone.utc).isoformat(),
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "overall_score": overall,
            "grade": _grade(overall),
            "duration_ms": duration_ms,
            "suite_revision": str(suite.get("revision") or ""),
            "registry_revision": str(dimensions["registry"].get("registry_revision") or ""),
            "dimensions": dimensions,
            "weights": DIMENSION_WEIGHTS,
            "error": "",
        }
        report["markdown"] = _render_markdown(report)
        row.status = "succeeded"
        row.overall_score = overall
        row.duration_ms = duration_ms
        row.suite_revision = report["suite_revision"]
        row.registry_revision = report["registry_revision"]
        row.report_json = json.dumps(report, ensure_ascii=False)
        row.finished_at = utcnow()
        row.error = ""
        db.commit()
        db.refresh(row)
        try:
            from aulos_knowledge.diagnosis import diagnose_benchmark_run

            diagnose_benchmark_run(db, row.id)
        except Exception:  # noqa: BLE001
            logger.exception("auto_diagnosis_failed run_id=%s", row.id)
        return report
    except Exception as exc:  # noqa: BLE001
        row.status = "failed"
        row.error = str(exc)[:2000]
        row.finished_at = utcnow()
        row.duration_ms = int((time.perf_counter() - t0) * 1000)
        db.commit()
        raise


def benchmark_run_summary(row: BenchmarkRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "status": row.status,
        "trigger": row.trigger,
        "overall_score": row.overall_score,
        "grade": _grade(row.overall_score) if row.status == "succeeded" else None,
        "duration_ms": row.duration_ms,
        "suite_revision": row.suite_revision,
        "registry_revision": row.registry_revision,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "error": row.error or "",
        "task_type": "knowledge.benchmark",
    }


def list_benchmark_runs(db: Session, *, limit: int = 20) -> list[dict[str, Any]]:
    rows = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).limit(min(limit, 100)).all()
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                **benchmark_run_summary(r),
                "grade": _grade(r.overall_score) if r.status == "succeeded" else None,
            }
        )
    return out


def get_benchmark_run(db: Session, run_id: int) -> dict[str, Any] | None:
    row = db.get(BenchmarkRun, run_id)
    if not row:
        return None
    if row.status in ("queued", "running"):
        return benchmark_run_summary(row)
    try:
        report = json.loads(row.report_json or "{}")
        if report:
            report["status"] = row.status
            report["error"] = row.error or ""
            return report
    except json.JSONDecodeError:
        pass
    return benchmark_run_summary(row)


def _health_status(score: float, has_run: bool) -> str:
    if not has_run:
        return "no_data"
    if score >= 80:
        return "healthy"
    if score >= 60:
        return "watch"
    return "critical"


def _build_insights(latest: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not latest:
        return [
            {
                "severity": "info",
                "title": "No benchmark baseline yet",
                "detail": "Run KB-BENCH-001 after catalog import or source crawl to establish a score.",
                "action": "run_benchmark",
            }
        ]

    insights: list[dict[str, Any]] = []
    dims = latest.get("dimensions") or {}

    retrieval = dims.get("retrieval") or {}
    if float(retrieval.get("score") or 0) < 80:
        failed = [
            c
            for c in list(retrieval.get("cases") or [])
            if not c.get("passed") and not c.get("optional")
        ]
        if failed:
            names = ", ".join(str(c.get("id")) for c in failed[:3])
            insights.append(
                {
                    "severity": "critical" if float(retrieval.get("score") or 0) < 60 else "warn",
                    "title": "Retrieval suite below target",
                    "detail": f"Failed cases: {names}. Check work_id filters and published corpus.",
                    "action": "simulate_rag",
                }
            )

    corpus = dims.get("corpus") or {}
    if float(corpus.get("publish_ratio") or 0) < 0.7 and int(corpus.get("documents") or 0) > 0:
        insights.append(
            {
                "severity": "warn",
                "title": "Low publish ratio",
                "detail": (
                    f"{corpus.get('published', 0)}/{corpus.get('documents', 0)} documents published "
                    f"({round(float(corpus.get('publish_ratio') or 0) * 100)}%). Review quarantine queue."
                ),
                "action": "review_documents",
            }
        )

    registry = dims.get("registry") or {}
    crawl_ready = int(registry.get("sources_crawl_ready") or 0)
    sources_total = int(registry.get("sources_total") or 0)
    if sources_total and crawl_ready < sources_total:
        insights.append(
            {
                "severity": "info",
                "title": "Registry not fully crawl-ready",
                "detail": f"{crawl_ready}/{sources_total} sources verified, enabled, and connector-ready.",
                "action": "verify_sources",
            }
        )

    provenance = dims.get("provenance") or {}
    if float(provenance.get("complete_ratio") or 1) < 0.9 and int(provenance.get("published_docs") or 0) > 0:
        insights.append(
            {
                "severity": "warn",
                "title": "Provenance gaps on published docs",
                "detail": (
                    f"{provenance.get('complete_provenance', 0)}/{provenance.get('published_docs', 0)} "
                    "published docs have full source+artifact+job lineage."
                ),
                "action": "audit_provenance",
            }
        )

    pipeline = dims.get("pipeline") or {}
    if pipeline.get("success_ratio") is not None and float(pipeline["success_ratio"]) < 0.85:
        insights.append(
            {
                "severity": "warn",
                "title": "Ingest pipeline instability",
                "detail": (
                    f"Recent job success {round(float(pipeline['success_ratio']) * 100)}% "
                    f"({pipeline.get('succeeded', 0)} ok / {pipeline.get('failed', 0)} failed)."
                ),
                "action": "inspect_jobs",
            }
        )

    if not insights:
        insights.append(
            {
                "severity": "ok",
                "title": "Knowledge plane performing within targets",
                "detail": "All benchmark dimensions are above operational thresholds.",
                "action": None,
            }
        )
    return insights


def _render_dashboard_markdown(payload: dict[str, Any]) -> str:
    latest = payload.get("latest_run")
    lines = [
        "# Knowledge performance dashboard",
        "",
        f"- **Generated:** {payload.get('generated_at')}",
        f"- **Health:** {payload.get('health_status')}",
        f"- **Headline:** {payload.get('headline')}",
        "",
    ]
    if latest:
        lines.extend(
            [
                f"- **Latest run:** #{latest.get('id')} · {latest.get('overall_score')} ({latest.get('grade')})",
                f"- **Suite:** {latest.get('suite_revision') or '—'} · **Registry:** {latest.get('registry_revision') or '—'}",
                "",
                "## Dimensions",
                "",
            ]
        )
        for dim in payload.get("dimensions") or []:
            lines.append(f"- **{dim.get('label')}** — {dim.get('score')} (weight {dim.get('weight_pct')}%)")
        lines.extend(["", "## Insights", ""])
        for ins in payload.get("insights") or []:
            lines.append(f"- [{ins.get('severity')}] {ins.get('title')}: {ins.get('detail')}")
    else:
        lines.append("_No benchmark runs recorded — run evaluation to populate this dashboard._")
    lines.append("")
    return "\n".join(lines)


def build_dashboard_report(db: Session) -> dict[str, Any]:
    """Aggregate latest benchmark + trend + insights for OPS dashboard."""
    suite = load_benchmark_suite()
    rows = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).limit(20).all()
    succeeded_rows = [r for r in rows if r.status == "succeeded"]
    active_row = next((r for r in rows if r.status in ("queued", "running")), None)
    trend = [
        {
            "id": r.id,
            "score": r.overall_score,
            "grade": _grade(r.overall_score),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reversed(succeeded_rows[:12])
    ]

    latest_report: dict[str, Any] | None = None
    previous_run: dict[str, Any] | None = None
    if succeeded_rows:
        latest_report = get_benchmark_run(db, succeeded_rows[0].id)
        if len(succeeded_rows) > 1:
            prev = succeeded_rows[1]
            previous_run = {
                "id": prev.id,
                "overall_score": prev.overall_score,
                "grade": _grade(prev.overall_score),
                "created_at": prev.created_at.isoformat() if prev.created_at else None,
            }

    score_delta: float | None = None
    if latest_report and previous_run:
        score_delta = round(float(latest_report["overall_score"]) - float(previous_run["overall_score"]), 2)

    dimensions_out: list[dict[str, Any]] = []
    retrieval_summary: dict[str, Any] = {"passed": 0, "total": 0, "failed_cases": []}
    if latest_report:
        for key, label in DIMENSION_LABELS.items():
            dim = dict((latest_report.get("dimensions") or {}).get(key) or {})
            score = float(dim.pop("score", 0))
            cases = dim.pop("cases", None)
            dimensions_out.append(
                {
                    "id": key,
                    "label": label,
                    "score": score,
                    "weight_pct": int(DIMENSION_WEIGHTS[key] * 100),
                    "details": dim,
                }
            )
        retrieval = (latest_report.get("dimensions") or {}).get("retrieval") or {}
        cases = list(retrieval.get("cases") or [])
        required = [c for c in cases if not c.get("optional")]
        failed = [c for c in required if not c.get("passed")]
        retrieval_summary = {
            "passed": sum(1 for c in required if c.get("passed")),
            "total": len(required),
            "failed_cases": [
                {"id": c.get("id"), "label": c.get("label"), "notes": c.get("notes") or []}
                for c in failed
            ],
        }

    overall = float(latest_report["overall_score"]) if latest_report else 0.0
    has_run = latest_report is not None
    health = _health_status(overall, has_run)

    if not has_run:
        headline = "Awaiting first benchmark run"
    elif health == "healthy":
        headline = f"Knowledge plane healthy — overall {overall} ({latest_report['grade']})"
    elif health == "watch":
        headline = f"Knowledge plane needs attention — overall {overall} ({latest_report['grade']})"
    else:
        headline = f"Knowledge plane below target — overall {overall} ({latest_report['grade']})"

    latest_summary = None
    if latest_report:
        latest_summary = {
            "id": latest_report.get("id"),
            "overall_score": latest_report.get("overall_score"),
            "grade": latest_report.get("grade"),
            "duration_ms": latest_report.get("duration_ms"),
            "suite_revision": latest_report.get("suite_revision"),
            "registry_revision": latest_report.get("registry_revision"),
            "created_at": latest_report.get("created_at"),
            "trigger": latest_report.get("trigger"),
        }

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "health_status": health,
        "headline": headline,
        "suite_revision": str(suite.get("revision") or ""),
        "run_count": db.query(BenchmarkRun).count(),
        "active_run": benchmark_run_summary(active_row) if active_row else None,
        "latest_run": latest_summary,
        "previous_run": previous_run,
        "score_delta": score_delta,
        "trend": trend,
        "dimensions": dimensions_out,
        "retrieval_summary": retrieval_summary,
        "weights": DIMENSION_WEIGHTS,
    }
    payload["insights"] = _build_insights(latest_report)
    payload["markdown_summary"] = _render_dashboard_markdown(payload)
    return payload
