from aulos_api.routes.auth import router as auth_router
from aulos_api.routes.chat import router as chat_router
from aulos_api.routes.entities import router as entities_router
from aulos_api.routes.health import router as health_router
from aulos_api.routes.listening import router as listening_router
from aulos_api.routes.listening_diary import router as listening_diary_router
from aulos_api.routes.media import router as media_router
from aulos_api.routes.ops import router as ops_router

__all__ = [
    "auth_router",
    "chat_router",
    "entities_router",
    "health_router",
    "listening_router",
    "listening_diary_router",
    "media_router",
    "ops_router",
]
