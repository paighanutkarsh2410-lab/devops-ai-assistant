"""API routes for maintenance windows."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from models import get_db
from models.user import User
from utils.auth import get_current_user
from services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


class MaintenanceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str  # ISO format
    end_time: str
    affected_services: list = []
    planned_actions: list = []


class MaintenanceEnd(BaseModel):
    notes: Optional[str] = None


@router.post("/", status_code=201)
def schedule_maintenance(
    body: MaintenanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = MaintenanceService(db, str(user.id))
    return svc.schedule_maintenance(
        title=body.title,
        description=body.description,
        start_time=datetime.fromisoformat(body.start_time),
        end_time=datetime.fromisoformat(body.end_time),
        affected_services=body.affected_services,
        planned_actions=body.planned_actions,
    )


@router.get("/")
def list_maintenance(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MaintenanceService(db, str(user.id)).get_all(status, limit)


@router.get("/upcoming")
def upcoming_maintenance(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MaintenanceService(db, str(user.id)).get_upcoming(days)


@router.get("/check/{service_name}")
def check_maintenance(
    service_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MaintenanceService(db, str(user.id)).is_in_maintenance(service_name)


@router.post("/{window_id}/start")
def start_maintenance(
    window_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MaintenanceService(db, str(user.id)).start_maintenance(window_id)


@router.post("/{window_id}/end")
def end_maintenance(
    window_id: str,
    body: MaintenanceEnd = MaintenanceEnd(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MaintenanceService(db, str(user.id)).end_maintenance(window_id, body.notes)


@router.post("/{window_id}/cancel")
def cancel_maintenance(
    window_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MaintenanceService(db, str(user.id)).cancel_maintenance(window_id)
