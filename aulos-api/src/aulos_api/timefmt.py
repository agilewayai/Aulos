"""UTC storage / wire formatting for Aulos API payloads.

Contract: store and emit UTC only (ISO-8601 with explicit ``Z``). User-facing
UIs format into the OS / browser timezone; they must not receive naive local
wall-clock strings.
"""

from __future__ import annotations

from datetime import datetime, timezone


def ensure_utc(dt: datetime) -> datetime:
    """Normalize aware or naive datetimes to UTC. Naive values are treated as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_utc_iso(dt: datetime) -> str:
    """Return an ISO-8601 UTC timestamp ending in ``Z``."""
    utc = ensure_utc(dt)
    timespec = "microseconds" if utc.microsecond else "seconds"
    return utc.isoformat(timespec=timespec).replace("+00:00", "Z")


def to_utc_iso_optional(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return to_utc_iso(dt)
