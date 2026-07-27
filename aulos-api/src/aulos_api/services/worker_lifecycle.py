"""Background worker start/stop/reset contracts (AUDIT-009 F8)."""

from __future__ import annotations


def shutdown_workers() -> None:
    from aulos_api.services.db_ha import stop_ha_worker
    from aulos_api.services.listening_queue import stop_listening_worker
    from aulos_api.services.mail_queue import stop_mail_worker

    stop_listening_worker()
    stop_mail_worker()
    stop_ha_worker()


def reset_all_workers_for_tests() -> None:
    """Stop workers and clear module globals so the next app fixture gets a clean slate."""
    shutdown_workers()
    from aulos_api.services import db_ha
    from aulos_api.services.listening_queue import reset_listening_worker_for_tests
    from aulos_api.services.mail_queue import reset_mail_worker_for_tests

    reset_listening_worker_for_tests()
    reset_mail_worker_for_tests()
    db_ha.reset_ha_worker_for_tests()
