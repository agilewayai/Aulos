"""Shared pytest hooks for API worker lifecycle isolation (AUDIT-009 F8)."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_background_workers() -> None:
    from aulos_api.services.worker_lifecycle import reset_all_workers_for_tests

    reset_all_workers_for_tests()
    yield
    reset_all_workers_for_tests()


def clear_session(client) -> None:
    """Drop HttpOnly session cookie so unauthenticated requests stay unauthenticated."""
    client.cookies.pop("aulos_session", None)
