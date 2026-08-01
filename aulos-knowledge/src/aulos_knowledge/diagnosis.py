"""KB-DIAG-001 — Benchmark diagnosis & improvement recommendations."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.benchmark import get_benchmark_run
from aulos_knowledge.connectors import connector_registered
from aulos_knowledge.db import (
    BenchmarkDiagnosis,
    BenchmarkRun,
    FetchJob,
    ImprovementAction,
    SourceAuthority,
    utcnow,
)

logger = logging.getLogger("aulos_knowledge.diagnosis")

# Crawl hints keyed by benchmark case id
CASE_CRAWL_HINTS: dict[str, dict[str, Any]] = {
    "cello-suites-filter": {
        "composer_id": "johann-sebastian-bach",
        "work_id": "bach.cello-suites.bwv-1007-1012",
        "wikipedia_titles": ["Cello Suites (Bach)", "Suite for Solo Cello No. 1 (Bach)"],
        "wikidata_qid": "Q1339",
    },
    "goldberg-filter": {
        "composer_id": "johann-sebastian-bach",
        "work_id": "bach.goldberg-variations.bwv-988",
        "wikipedia_titles": ["Goldberg Variations"],
        "wikidata_qid": "Q1339",
    },
    "bach-composer-browse": {
        "composer_id": "johann-sebastian-bach",
        "work_id": "",
        "wikipedia_titles": ["Johann Sebastian Bach"],
        "wikidata_qid": "Q1339",
    },
    "mozart-requiem": {
        "composer_id": "wolfgang-amadeus-mozart",
        "work_id": "",
        "wikipedia_titles": ["Requiem (Mozart)"],
        "wikidata_qid": "Q254",
    },
}


def _source_crawlable(db: Session, source_id: str) -> bool:
    src = db.get(SourceAuthority, source_id)
    if not src:
        return False
    return (
        (src.verification_status or "") == "verified"
        and bool(src.enabled)
        and connector_registered(src.connector or "")
    )


def _action(
    *,
    item_id: str,
    action_type: str,
    layer: str,
    auto_safe: bool,
    title: str,
    detail: str,
    payload: dict[str, Any],
    expected_lift: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "action_type": action_type,
        "layer": layer,
        "auto_safe": auto_safe,
        "title": title,
        "detail": detail,
        "payload": payload,
        "expected_lift": expected_lift or {},
        "status": "proposed",
    }


def _diagnose_retrieval_case(
    db: Session,
    case: dict[str, Any],
    *,
    item_idx: int,
) -> dict[str, Any] | None:
    if case.get("passed") or case.get("optional"):
        return None
    cid = str(case.get("id") or f"case-{item_idx}")
    notes = list(case.get("notes") or [])
    hits = int(case.get("hits") or 0)
    hints = CASE_CRAWL_HINTS.get(cid, {})
    composer_id = hints.get("composer_id", "")
    work_id = hints.get("work_id", "")
    actions: list[dict[str, Any]] = []

    bleed = any("forbidden token" in n.lower() or "work_id mismatch" in n.lower() for n in notes)
    if bleed:
        root = "WORK_ID_FILTER_LEAK"
        actions.append(
            _action(
                item_id=f"{cid}-eng-retrieve",
                action_type="engineering_task",
                layer="L3",
                auto_safe=False,
                title="Harden retrieval work_id isolation",
                detail=(
                    f"Case `{cid}` shows identity bleed in hits. Review retrieve() filters in "
                    "aulos_knowledge/retrieve.py and add regression in tests/test_work_id_rag.py."
                ),
                payload={
                    "spec_hint": "SPEC-009",
                    "files": ["aulos_knowledge/retrieve.py", "tests/test_work_id_rag.py"],
                    "acceptance": f"benchmark case {cid} passes",
                    "case_id": cid,
                },
                expected_lift={"dimension": "retrieval", "min_delta": 20},
            )
        )
    elif hits == 0:
        root = "RETRIEVAL_NO_HITS"
        if _source_crawlable(db, "wikipedia") and hints.get("wikipedia_titles"):
            actions.append(
                _action(
                    item_id=f"{cid}-crawl-wikipedia",
                    action_type="crawl_source",
                    layer="L1",
                    auto_safe=True,
                    title=f"Crawl Wikipedia for {cid}",
                    detail=f"Fetch authority summaries for: {', '.join(hints['wikipedia_titles'])}",
                    payload={
                        "source_id": "wikipedia",
                        "params": {
                            "titles": hints["wikipedia_titles"],
                            "langs": ["en", "zh"],
                            "composer_id": composer_id,
                            "aulos_work_id": work_id,
                        },
                    },
                    expected_lift={"dimension": "retrieval", "min_delta": 15},
                )
            )
        if _source_crawlable(db, "wikidata") and hints.get("wikidata_qid"):
            actions.append(
                _action(
                    item_id=f"{cid}-crawl-wikidata",
                    action_type="crawl_source",
                    layer="L1",
                    auto_safe=True,
                    title=f"Crawl Wikidata seed for {cid}",
                    detail=f"Enrich composer entity via QID {hints['wikidata_qid']}",
                    payload={
                        "source_id": "wikidata",
                        "params": {"qids": [hints["wikidata_qid"]], "composer_id": composer_id},
                    },
                )
            )
        if _source_crawlable(db, "catalog-local"):
            actions.append(
                _action(
                    item_id=f"{cid}-catalog-import",
                    action_type="crawl_source",
                    layer="L1",
                    auto_safe=True,
                    title="Refresh catalog-local corpus",
                    detail="Re-import curated catalog YAML to seed published work documents.",
                    payload={"source_id": "catalog-local", "params": {}},
                )
            )
        if hints.get("wikidata_qid"):
            titles = hints.get("wikipedia_titles") or []
            actions.append(
                _action(
                    item_id=f"{cid}-explore-sources",
                    action_type="explore_sources",
                    layer="L1",
                    auto_safe=True,
                    title=f"Explore authority sources for {cid}",
                    detail="REQ-009 graph discover + enqueue verified authority crawls.",
                    payload={
                        "composer_id": composer_id,
                        "wikidata_qid": hints["wikidata_qid"],
                        "wikipedia_title": titles[0] if titles else "",
                        "enqueue_crawl": True,
                        "max_depth": 2,
                    },
                    expected_lift={"dimension": "retrieval", "min_delta": 10},
                )
            )
    else:
        root = "RETRIEVAL_LOW_SCORE"
        actions.append(
            _action(
                item_id=f"{cid}-eng-scoring",
                action_type="engineering_task",
                layer="L3",
                auto_safe=False,
                title="Improve lexical retrieval scoring",
                detail=(
                    f"Case `{cid}` returns hits but below min_top_score. Consider chunking, "
                    "synonym expansion, or embedding retrieval (SPEC-009)."
                ),
                payload={
                    "spec_hint": "SPEC-009",
                    "files": ["aulos_knowledge/retrieve.py"],
                    "acceptance": f"top_score meets suite threshold for {cid}",
                    "case_id": cid,
                },
                expected_lift={"dimension": "retrieval", "min_delta": 10},
            )
        )

    severity = "critical" if bleed or hits == 0 else "warn"
    return {
        "id": cid,
        "dimension": "retrieval",
        "severity": severity,
        "root_cause_code": root,
        "title": str(case.get("label") or cid),
        "detail": "; ".join(notes) if notes else f"hits={hits} top={case.get('top_score')}",
        "evidence": {
            "case_id": cid,
            "hits": hits,
            "top_score": case.get("top_score"),
            "notes": notes,
            "hits_preview": case.get("hits_preview") or [],
        },
        "actions": actions,
    }


def _diagnose_dimensions(
    db: Session,
    report: dict[str, Any],
    *,
    prev_report: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    dims = report.get("dimensions") or {}

    retrieval = dims.get("retrieval") or {}
    for i, case in enumerate(list(retrieval.get("cases") or [])):
        if not isinstance(case, dict):
            continue
        item = _diagnose_retrieval_case(db, case, item_idx=i)
        if item:
            items.append(item)

    corpus = dims.get("corpus") or {}
    publish_ratio = float(corpus.get("publish_ratio") or 0)
    if publish_ratio < 0.85 and int(corpus.get("documents") or 0) > 0:
        actions = []
        if _source_crawlable(db, "catalog-local"):
            actions.append(
                _action(
                    item_id="corpus-catalog",
                    action_type="crawl_source",
                    layer="L1",
                    auto_safe=True,
                    title="Re-import catalog-local",
                    detail="Refresh published catalog documents.",
                    payload={"source_id": "catalog-local", "params": {}},
                    expected_lift={"dimension": "corpus", "min_delta": 10},
                )
            )
        actions.append(
            _action(
                item_id="corpus-review-quarantine",
                action_type="review_quarantine",
                layer="L2",
                auto_safe=False,
                title="Review quarantined documents",
                detail=(
                    f"{corpus.get('quarantine', 0)} docs in quarantine — proofread and publish "
                    "authority-tier content."
                ),
                payload={"filter": {"status": "quarantine"}},
            )
        )
        items.append(
            {
                "id": "corpus-low-publish",
                "dimension": "corpus",
                "severity": "warn" if publish_ratio >= 0.5 else "critical",
                "root_cause_code": "CORPUS_LOW_PUBLISH",
                "title": "Low publish ratio",
                "detail": (
                    f"{corpus.get('published', 0)}/{corpus.get('documents', 0)} published "
                    f"({round(publish_ratio * 100)}%)"
                ),
                "evidence": corpus,
                "actions": actions,
            }
        )

    work_cov = float(corpus.get("work_coverage_ratio") or 0)
    if work_cov < 0.4 and int(corpus.get("works_total") or 0) > 0:
        items.append(
            {
                "id": "corpus-work-gap",
                "dimension": "corpus",
                "severity": "info",
                "root_cause_code": "CORPUS_WORK_GAP",
                "title": "Works lack published knowledge docs",
                "detail": (
                    f"{corpus.get('works_with_published_docs', 0)}/"
                    f"{corpus.get('works_total', 0)} works covered"
                ),
                "evidence": corpus,
                "actions": [
                    _action(
                        item_id="corpus-work-crawl",
                        action_type="crawl_authority_bundle",
                        layer="L1",
                        auto_safe=True,
                        title="Crawl authority bundle for Bach seed",
                        detail="Wikipedia + Wikidata for primary catalog composer.",
                        payload={
                            "composer_id": "johann-sebastian-bach",
                            "wikidata_qid": "Q1339",
                            "wikipedia_title": "Johann Sebastian Bach",
                        },
                        expected_lift={"dimension": "corpus", "min_delta": 5},
                    ),
                    _action(
                        item_id="corpus-work-explore",
                        action_type="explore_sources",
                        layer="L1",
                        auto_safe=True,
                        title="Explore authority sources for Bach seed",
                        detail=(
                            "REQ-009 graph search from Wikidata Q1339; enqueue verified "
                            "authority crawls and surface new candidate sources."
                        ),
                        payload={
                            "composer_id": "johann-sebastian-bach",
                            "wikidata_qid": "Q1339",
                            "wikipedia_title": "Johann Sebastian Bach",
                            "enqueue_crawl": True,
                            "max_depth": 2,
                        },
                        expected_lift={"dimension": "registry", "min_delta": 5},
                    ),
                ],
            }
        )

    registry = dims.get("registry") or {}
    crawl_ready = int(registry.get("sources_crawl_ready") or 0)
    sources_total = int(registry.get("sources_total") or 0)
    if sources_total and crawl_ready < sources_total:
        blocked = []
        for src in db.query(SourceAuthority).order_by(SourceAuthority.id).all():
            if _source_crawlable(db, src.id):
                continue
            blocked.append(
                {
                    "id": src.id,
                    "verification_status": src.verification_status,
                    "enabled": src.enabled,
                    "connector": src.connector,
                }
            )
        items.append(
            {
                "id": "registry-gates",
                "dimension": "registry",
                "severity": "info",
                "root_cause_code": "REGISTRY_NOT_CRAWL_READY",
                "title": "Sources blocked from crawl",
                "detail": f"{crawl_ready}/{sources_total} crawl-ready",
                "evidence": {"blocked_sources": blocked, **registry},
                "actions": [
                    _action(
                        item_id="registry-verify",
                        action_type="verify_sources",
                        layer="L2",
                        auto_safe=False,
                        title="Verify and enable authority sources",
                        detail="Complete REQ-008 gates for candidate sources in registry.",
                        payload={"module": "registry"},
                    ),
                    _action(
                        item_id="registry-explore",
                        action_type="explore_sources",
                        layer="L1",
                        auto_safe=True,
                        title="Explore more authority sources",
                        detail=(
                            "Run REQ-009 discovery to find and score new candidates; "
                            "register high-score domains for human verify."
                        ),
                        payload={
                            "wikidata_qid": "Q1339",
                            "composer_id": "johann-sebastian-bach",
                            "enqueue_crawl": True,
                            "max_depth": 2,
                        },
                    ),
                ],
            }
        )

    provenance = dims.get("provenance") or {}
    if float(provenance.get("complete_ratio") or 1) < 0.9 and int(provenance.get("published_docs") or 0) > 0:
        items.append(
            {
                "id": "provenance-gaps",
                "dimension": "provenance",
                "severity": "warn",
                "root_cause_code": "PROVENANCE_INCOMPLETE",
                "title": "Incomplete provenance on published docs",
                "detail": (
                    f"{provenance.get('complete_provenance', 0)}/"
                    f"{provenance.get('published_docs', 0)} with full lineage"
                ),
                "evidence": provenance,
                "actions": [
                    _action(
                        item_id="provenance-reingest",
                        action_type="crawl_source",
                        layer="L1",
                        auto_safe=True,
                        title="Re-run catalog import for provenance baseline",
                        detail="Catalog-local jobs attach source+artifact+job on ingest.",
                        payload={"source_id": "catalog-local", "params": {}},
                    )
                ],
            }
        )

    pipeline = dims.get("pipeline") or {}
    if pipeline.get("success_ratio") is not None and float(pipeline["success_ratio"]) < 0.85:
        failed_jobs = (
            db.query(FetchJob)
            .filter(FetchJob.status == "failed")
            .order_by(FetchJob.id.desc())
            .limit(5)
            .all()
        )
        items.append(
            {
                "id": "pipeline-failures",
                "dimension": "pipeline",
                "severity": "warn",
                "root_cause_code": "PIPELINE_JOB_FAILURE",
                "title": "Recent ingest job failures",
                "detail": (
                    f"Success {round(float(pipeline['success_ratio']) * 100)}% "
                    f"({pipeline.get('succeeded', 0)} ok / {pipeline.get('failed', 0)} failed)"
                ),
                "evidence": {
                    **pipeline,
                    "recent_failures": [
                        {"id": j.id, "source_id": j.source_id, "error": (j.error or "")[:200]}
                        for j in failed_jobs
                    ],
                },
                "actions": [
                    _action(
                        item_id="pipeline-inspect",
                        action_type="inspect_jobs",
                        layer="L2",
                        auto_safe=False,
                        title="Inspect failed jobs",
                        detail="Review errors and fix connector/URL policy issues.",
                        payload={"module": "jobs", "status": "failed"},
                    )
                ],
            }
        )

    if prev_report and float(report.get("overall_score") or 0) < float(prev_report.get("overall_score") or 0) - 5:
        items.append(
            {
                "id": "score-regression",
                "dimension": "meta",
                "severity": "critical",
                "root_cause_code": "SCORE_REGRESSION",
                "title": "Benchmark score regressed vs prior run",
                "detail": (
                    f"{report.get('overall_score')} vs {prev_report.get('overall_score')} "
                    f"(run #{prev_report.get('id')})"
                ),
                "evidence": {
                    "current_score": report.get("overall_score"),
                    "previous_score": prev_report.get("overall_score"),
                    "previous_run_id": prev_report.get("id"),
                },
                "actions": [
                    _action(
                        item_id="regression-harness",
                        action_type="engineering_task",
                        layer="L3",
                        auto_safe=False,
                        title="Investigate benchmark regression",
                        detail="Compare runs in JOURNAL; do not lower suite thresholds without REQ.",
                        payload={"spec_hint": "SPEC-009", "harness": "aulos-knowledge/.aries_harness/JOURNAL.md"},
                    )
                ],
            }
        )

    if not items:
        items.append(
            {
                "id": "all-clear",
                "dimension": "meta",
                "severity": "ok",
                "root_cause_code": "HEALTHY",
                "title": "No blocking issues detected",
                "detail": "Benchmark within targets; schedule periodic re-evaluation after ingest.",
                "evidence": {"overall_score": report.get("overall_score")},
                "actions": [],
            }
        )
    return items


def _render_diagnosis_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# KB-DIAG-001 — Diagnosis for benchmark run #{payload.get('benchmark_run_id')}",
        "",
        f"- **Score:** {payload.get('overall_score')} ({payload.get('grade')})",
        f"- **Items:** {len(payload.get('items') or [])}",
        f"- **Auto-safe actions:** {payload.get('auto_safe_count', 0)}",
        "",
        "## Findings",
        "",
    ]
    for item in payload.get("items") or []:
        lines.append(
            f"### [{item.get('severity')}] {item.get('root_cause_code')} — {item.get('title')}"
        )
        lines.append(f"{item.get('detail')}")
        for act in item.get("actions") or []:
            mark = "AUTO" if act.get("auto_safe") else act.get("layer", "L?")
            lines.append(f"- **{mark}** {act.get('title')}: {act.get('detail')}")
        lines.append("")
    l3 = payload.get("engineering_tasks") or []
    if l3:
        lines.extend(["## Engineering tasks (L3)", ""])
        for t in l3:
            lines.append(f"- {t.get('title')}: {t.get('detail')}")
        lines.append("")
    return "\n".join(lines)


def diagnose_benchmark_run(db: Session, run_id: int, *, persist: bool = True) -> dict[str, Any]:
    """Generate structured diagnosis + improvement actions for a succeeded benchmark run."""
    report = get_benchmark_run(db, run_id)
    if not report or report.get("status") != "succeeded":
        raise ValueError(f"benchmark run {run_id} not available for diagnosis")

    prev_row = (
        db.query(BenchmarkRun)
        .filter(BenchmarkRun.id < run_id, BenchmarkRun.status == "succeeded")
        .order_by(BenchmarkRun.id.desc())
        .first()
    )
    prev_report = get_benchmark_run(db, prev_row.id) if prev_row else None

    items = _diagnose_dimensions(db, report, prev_report=prev_report)
    all_actions: list[dict[str, Any]] = []
    for item in items:
        for act in item.get("actions") or []:
            all_actions.append(act)

    engineering = [
        {
            "title": a["title"],
            "detail": a["detail"],
            "payload": a.get("payload") or {},
            "item_id": a.get("item_id"),
        }
        for a in all_actions
        if a.get("layer") == "L3"
    ]

    payload: dict[str, Any] = {
        "benchmark_run_id": run_id,
        "diagnosed_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": report.get("overall_score"),
        "grade": report.get("grade"),
        "previous_run_id": prev_report.get("id") if prev_report else None,
        "score_delta": (
            round(float(report["overall_score"]) - float(prev_report["overall_score"]), 2)
            if prev_report
            else None
        ),
        "items": items,
        "action_count": len(all_actions),
        "auto_safe_count": sum(1 for a in all_actions if a.get("auto_safe")),
        "engineering_tasks": engineering,
    }
    payload["markdown"] = _render_diagnosis_markdown(payload)

    if not persist:
        return payload

    existing = (
        db.query(BenchmarkDiagnosis)
        .filter(BenchmarkDiagnosis.benchmark_run_id == run_id)
        .order_by(BenchmarkDiagnosis.id.desc())
        .first()
    )
    if existing:
        diag_row = existing
        diag_row.status = "open"
        diag_row.diagnosis_json = json.dumps(payload, ensure_ascii=False)
        diag_row.markdown = payload["markdown"]
        db.query(ImprovementAction).filter(ImprovementAction.diagnosis_id == diag_row.id).delete()
    else:
        diag_row = BenchmarkDiagnosis(
            benchmark_run_id=run_id,
            status="open",
            diagnosis_json=json.dumps(payload, ensure_ascii=False),
            markdown=payload["markdown"],
        )
        db.add(diag_row)
        db.flush()

    for item in items:
        for act in item.get("actions") or []:
            db.add(
                ImprovementAction(
                    diagnosis_id=diag_row.id,
                    item_id=str(act.get("item_id") or ""),
                    action_type=str(act.get("action_type") or ""),
                    layer=str(act.get("layer") or "L1"),
                    auto_safe=bool(act.get("auto_safe")),
                    status="proposed",
                    payload_json=json.dumps(act.get("payload") or {}, ensure_ascii=False),
                )
            )
    db.commit()
    db.refresh(diag_row)
    payload["diagnosis_id"] = diag_row.id
    payload["id"] = diag_row.id
    return payload


def get_diagnosis_for_run(db: Session, run_id: int) -> dict[str, Any] | None:
    row = (
        db.query(BenchmarkDiagnosis)
        .filter(BenchmarkDiagnosis.benchmark_run_id == run_id)
        .order_by(BenchmarkDiagnosis.id.desc())
        .first()
    )
    if not row:
        return None
    try:
        out = json.loads(row.diagnosis_json or "{}")
    except json.JSONDecodeError:
        out = {}
    out["diagnosis_id"] = row.id
    out["id"] = row.id
    out["status"] = row.status
    out["actions"] = list_improvement_actions(db, diagnosis_id=row.id)
    return out


def list_improvement_actions(db: Session, *, diagnosis_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(ImprovementAction)
        .filter(ImprovementAction.diagnosis_id == diagnosis_id)
        .order_by(ImprovementAction.id.asc())
        .all()
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        try:
            payload = json.loads(r.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        try:
            result = json.loads(r.result_json or "{}")
        except json.JSONDecodeError:
            result = {}
        out.append(
            {
                "id": r.id,
                "diagnosis_id": r.diagnosis_id,
                "item_id": r.item_id,
                "action_type": r.action_type,
                "layer": r.layer,
                "auto_safe": r.auto_safe,
                "status": r.status,
                "payload": payload,
                "result": result,
                "error": r.error or "",
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "executed_at": r.executed_at.isoformat() if r.executed_at else None,
            }
        )
    return out
