"""Ops background task queue routes (SPEC-018)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import require_roles
from aulos_api.db.models import User
from aulos_api.db.session import get_db

router = APIRouter()


class OpsTaskOut(BaseModel):
    id: int
    task_type: str
    source: str
    status: str
    payload: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    error_detail: str = ""
    created_by_user_id: int | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None


@router.get("/tasks/dashboard")
def tasks_dashboard(
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> dict:
    from aulos_api.services.task_queue import dashboard

    return dashboard(db)


@router.get("/tasks", response_model=list[OpsTaskOut])
def list_ops_tasks(
    status: str | None = None,
    task_type: str | None = None,
    source: str | None = None,
    limit: int = 50,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> list[OpsTaskOut]:
    from aulos_api.services.task_queue import list_tasks

    return [OpsTaskOut(**row) for row in list_tasks(db, status=status, task_type=task_type, source=source, limit=limit)]


@router.get("/tasks/{task_id}", response_model=OpsTaskOut)
def get_ops_task(
    task_id: int,
    _: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
) -> OpsTaskOut:
    from aulos_api.services.task_queue import get_task, task_to_dict

    row = get_task(db, task_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return OpsTaskOut(**task_to_dict(row))
