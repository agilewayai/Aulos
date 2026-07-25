from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aulos_api.config import get_settings
from aulos_api.db.session import get_db
from aulos_api.services import AgentProxy

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    proxy = AgentProxy(settings)
    backends = await proxy.health_backends(db=db)
    return {
        "status": "ok",
        "service": "aulos-api",
        "version": "0.1.0",
        "backends": backends,
    }
