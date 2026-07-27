from contextlib import asynccontextmanager
import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aulos_api.config import get_settings
from aulos_api.routes import (
    auth_router,
    chat_router,
    health_router,
    listening_router,
    media_router,
    ops_router,
)
from aulos_api.security import AbuseDetector, RateLimitMiddleware
from aulos_api.services.bootstrap import bootstrap_identity
from aulos_api.services.mailgun import clear_fake_mailbox


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("aulos_api.mail").setLevel(logging.INFO)
    logging.getLogger("aulos_api.listening").setLevel(logging.INFO)
    logging.getLogger("aulos_api.security").setLevel(logging.INFO)
    logging.getLogger("aulos_api.media").setLevel(logging.INFO)


def _warm_media_cache() -> None:
    try:
        from aulos_api.services.media_cache import discover_corpus_audio_urls, prefetch_urls

        urls = discover_corpus_audio_urls()
        n = prefetch_urls(urls)
        logging.getLogger("aulos_api.media").info("media_prefetch done urls=%s cached=%s", len(urls), n)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("aulos_api.media").warning("media_prefetch_failed err=%s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _configure_logging()
    clear_fake_mailbox()
    bootstrap_identity()
    try:
        from aulos_api.services.db_ha import start_ha_worker

        start_ha_worker()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("aulos_api.db_ha").warning("db_ha_worker_skip err=%s", exc)
    try:
        from aulos_api.services.mail_queue import start_mail_worker

        start_mail_worker()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("aulos_api.mail_queue").warning("mail_worker_skip err=%s", exc)
    try:
        from aulos_api.services.listening_queue import start_listening_worker

        start_listening_worker()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("aulos_api.listening_queue").warning("listening_worker_skip err=%s", exc)
    try:
        from aulos_api.services.task_queue import start_task_worker

        start_task_worker()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("aulos_api.task_queue").warning("task_worker_skip err=%s", exc)
    threading.Thread(target=_warm_media_cache, name="aulos-media-prefetch", daemon=True).start()
    yield
    try:
        from aulos_api.services.worker_lifecycle import shutdown_workers

        shutdown_workers()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("aulos_api.app").warning("worker_shutdown_skip err=%s", exc)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Aulos API Gateway",
        version="0.1.0",
        description="HTTP gateway for Aulos web GUI, agents, and MCP integrations",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Outer-most after CORS registration order: last added runs first on request.
    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.rate_limit_enabled,
        trust_proxy=settings.trust_proxy,
        abuse=AbuseDetector(
            strike_limit=settings.abuse_strike_limit,
            window_sec=float(settings.abuse_strike_window_sec),
        ),
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(ops_router)
    app.include_router(listening_router)
    app.include_router(media_router)
    return app


app = create_app()
