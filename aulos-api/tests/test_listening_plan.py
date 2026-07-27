"""Unit tests for countable listening plan helpers."""

from __future__ import annotations

from aulos_api.services.listening_plan import (
    PLAN_TOTAL,
    initial_plan_steps,
    mark_stage,
    progress_counts,
    upsert_step,
)


def test_initial_plan_is_countable() -> None:
    steps = initial_plan_steps()
    assert len(steps) == PLAN_TOTAL
    assert all(s["status"] == "pending" for s in steps)
    assert steps[0]["id"] == "g.discogs"
    assert steps[-1]["id"] == "listening.eval"
    assert steps[0]["index"] == 1
    assert steps[-1]["index"] == PLAN_TOTAL
    assert steps[-1]["total"] == PLAN_TOTAL


def test_mark_stage_updates_and_progress() -> None:
    steps = initial_plan_steps()
    steps = mark_stage(steps, "g.discogs", status="running", detail="looking up release")
    steps = mark_stage(steps, "g.discogs", status="done", detail="ok")
    steps = mark_stage(steps, "g.identity", status="done", detail="locked")
    counts = progress_counts(steps)
    assert counts["done"] == 2
    assert counts["total"] == PLAN_TOTAL
    assert steps[0]["status"] == "done"


def test_upsert_unknown_step_extends_total() -> None:
    steps = initial_plan_steps()
    steps = upsert_step(
        steps,
        {"id": "extra.note", "title": "Extra", "status": "done", "thinking": "x", "detail": ""},
    )
    assert any(s["id"] == "extra.note" for s in steps)
    assert progress_counts(steps)["total"] >= PLAN_TOTAL
