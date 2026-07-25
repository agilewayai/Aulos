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
    out: dict = {
        "status": "ok",
        "service": "aulos-api",
        "version": "0.1.0",
        "backends": backends,
    }
    if (settings.db_failover_url or "").strip():
        try:
            from aulos_api.services import db_ha

            out["db_ha"] = {
                "active_role": db_ha.get_active_role(),
                "primary_ok": db_ha.ha_status()["primary"]["ok"],
                "failover_ok": db_ha.ha_status()["failover"]["ok"],
            }
        except Exception as exc:  # noqa: BLE001
            out["db_ha"] = {"error": str(exc)[:200]}
    return out
