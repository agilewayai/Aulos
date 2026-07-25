"""UTC wire-format contract for API timestamps."""

from datetime import datetime, timedelta, timezone

from aulos_api.timefmt import ensure_utc, to_utc_iso, to_utc_iso_optional


def test_to_utc_iso_aware_ends_with_z() -> None:
    dt = datetime(2026, 7, 25, 16, 30, 0, tzinfo=timezone.utc)
    assert to_utc_iso(dt) == "2026-07-25T16:30:00Z"


def test_to_utc_iso_naive_treated_as_utc() -> None:
    dt = datetime(2026, 7, 25, 16, 30, 0)  # naive
    assert to_utc_iso(dt).endswith("Z")
    assert to_utc_iso(dt).startswith("2026-07-25T16:30:00")


def test_to_utc_iso_converts_non_utc_offset() -> None:
    # UTC+8 wall clock 00:30 next day → previous day 16:30Z
    east = timezone(timedelta(hours=8))
    dt = datetime(2026, 7, 26, 0, 30, 0, tzinfo=east)
    assert to_utc_iso(dt) == "2026-07-25T16:30:00Z"


def test_to_utc_iso_optional_none() -> None:
    assert to_utc_iso_optional(None) is None


def test_ensure_utc_preserves_instant() -> None:
    east = timezone(timedelta(hours=8))
    dt = datetime(2026, 7, 26, 0, 30, 0, tzinfo=east)
    assert ensure_utc(dt) == datetime(2026, 7, 25, 16, 30, 0, tzinfo=timezone.utc)
