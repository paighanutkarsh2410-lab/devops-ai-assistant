"""API routes for SLA tracking — configs, status, error budgets."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from models import get_db
from models.user import User
from utils.auth import get_current_user
from services.sla_tracker import SLATracker

router = APIRouter(prefix="/sla", tags=["sla"])


class SLAConfigCreate(BaseModel):
    service_name: str
    target_uptime: float = 99.9
    max_mttr_minutes: int = 30
    max_incidents_per_month: Optional[int] = None


@router.get("/configs")
def list_configs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return SLATracker(db, str(user.id)).get_configs()


@router.post("/configs", status_code=201)
def create_config(
    body: SLAConfigCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return SLATracker(db, str(user.id)).create_config(
        body.service_name, body.target_uptime, body.max_mttr_minutes, body.max_incidents_per_month
    )


@router.get("/status")
def sla_status(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return SLATracker(db, str(user.id)).calculate_all_slas(days)


@router.get("/status/{service_name}")
def service_sla(
    service_name: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return SLATracker(db, str(user.id)).calculate_sla(service_name, days)
