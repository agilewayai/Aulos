"""Unit tests for countable listening plan helpers."""

from __future__ import annotations

from aulos_api.services.listening_plan import (
    PLAN_TOTAL,
    canonicalize_step_id,
    coalesce_plan_steps,
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
    assert any(s["id"] == "g.program" for s in steps)
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
    assert counts["completed"] == 2
    assert counts["skipped"] == 0
    assert counts["done"] == 2  # finished = completed + skipped + failed
    assert counts["total"] == PLAN_TOTAL
    assert steps[0]["status"] == "done"


def test_skip_counted_separately() -> None:
    steps = initial_plan_steps()
    steps = mark_stage(steps, "g.discogs", status="skip", detail="No /discogs command")
    steps = mark_stage(steps, "g.web", status="skipped", detail="shelf warm")
    steps = mark_stage(steps, "g.identity", status="done", detail="locked")
    counts = progress_counts(steps)
    assert counts["completed"] == 1
    assert counts["skipped"] == 2
    assert counts["done"] == 3
    assert counts["total"] == PLAN_TOTAL


def test_canonicalize_short_agent_ids() -> None:
    assert canonicalize_step_id("route") == "listening.route"
    assert canonicalize_step_id("listening.compose") == "listening.compose"
    assert canonicalize_step_id("g.web") == "g.web"
    assert canonicalize_step_id("review-compose") == "review-compose"


def test_upsert_short_agent_id_fills_placeholder() -> None:
    steps = initial_plan_steps()
    steps = upsert_step(
        steps,
        {
            "id": "route",
            "title": "Route",
            "status": "done",
            "thinking": "plan",
            "detail": "ok",
            "skill_id": "listening.route",
        },
    )
    ids = [s["id"] for s in steps]
    assert ids.count("listening.route") == 1
    assert "route" not in ids
    assert progress_counts(steps)["total"] == PLAN_TOTAL
    route = next(s for s in steps if s["id"] == "listening.route")
    assert route["status"] == "done"


def test_review_milestone_not_countable() -> None:
    steps = initial_plan_steps()
    steps = upsert_step(
        steps,
        {
            "id": "review-compose",
            "title": "Review (compose)",
            "status": "done",
            "thinking": "critic",
            "detail": "PASS",
            "skill_id": "listening.review",
        },
    )
    assert any(s["id"] == "review-compose" for s in steps)
    review = next(s for s in steps if s["id"] == "review-compose")
    assert review.get("countable") is False
    counts = progress_counts(steps)
    assert counts["total"] == PLAN_TOTAL


def test_upsert_unknown_step_extends_total() -> None:
    steps = initial_plan_steps()
    steps = upsert_step(
        steps,
        {"id": "extra.note", "title": "Extra", "status": "done", "thinking": "x", "detail": ""},
    )
    assert any(s["id"] == "extra.note" for s in steps)
    assert progress_counts(steps)["total"] >= PLAN_TOTAL


def test_coalesce_merges_short_ids_and_drops_ghost_pending() -> None:
    steps = initial_plan_steps()
    # Legacy shape: placeholders stay pending while short ids complete.
    steps.append(
        {
            "id": "route",
            "title": "Route",
            "status": "done",
            "thinking": "",
            "detail": "planned",
            "skill_id": "listening.route",
        }
    )
    steps.append(
        {
            "id": "compose",
            "title": "Compose",
            "status": "done",
            "thinking": "",
            "detail": "html",
            "skill_id": "listening.compose",
        }
    )
    steps.append(
        {
            "id": "review-compose",
            "title": "Review (compose)",
            "status": "done",
            "thinking": "",
            "detail": "PASS",
            "skill_id": "listening.review",
        }
    )
    fixed = coalesce_plan_steps(steps)
    ids = [s["id"] for s in fixed]
    assert "route" not in ids
    assert "compose" not in ids
    assert ids.count("listening.route") == 1
    assert ids.count("listening.compose") == 1
    assert next(s for s in fixed if s["id"] == "listening.route")["status"] == "done"
    assert next(s for s in fixed if s["id"] == "listening.compose")["status"] == "done"
    assert any(s["id"] == "review-compose" and s.get("countable") is False for s in fixed)
    counts = progress_counts(fixed)
    assert counts["total"] == PLAN_TOTAL
    pending_agent = [
        s for s in fixed if str(s["id"]).startswith("listening.") and s["status"] == "pending"
    ]
    assert all(s["id"] not in {"listening.route", "listening.compose"} for s in pending_agent)
