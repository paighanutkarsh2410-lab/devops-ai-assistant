"""API routes for chaos engineering experiments."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from models import get_db
from models.user import User
from utils.auth import get_current_user
from chaos.chaos_engine import ChaosEngine

router = APIRouter(prefix="/chaos", tags=["chaos"])


class ExperimentCreate(BaseModel):
    name: str
    experiment_type: str
    target_service: Optional[str] = None
    config: dict = {}
    duration_seconds: int = 60


@router.get("/types")
def experiment_types():
    """List available experiment types."""
    return ChaosEngine.EXPERIMENT_TYPES


@router.post("/experiments", status_code=201)
def create_experiment(
    body: ExperimentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChaosEngine(db, str(user.id)).create_experiment(
        name=body.name,
        experiment_type=body.experiment_type,
        target_service=body.target_service,
        config=body.config,
        duration_seconds=body.duration_seconds,
    )


@router.get("/experiments")
def list_experiments(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChaosEngine(db, str(user.id)).get_experiments(status, limit)


@router.post("/experiments/{experiment_id}/run")
def run_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChaosEngine(db, str(user.id)).run_experiment(experiment_id)


@router.post("/experiments/{experiment_id}/stop")
def stop_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChaosEngine(db, str(user.id)).stop_experiment(experiment_id)


@router.get("/experiments/{experiment_id}/results")
def experiment_results(
    experiment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChaosEngine(db, str(user.id)).get_experiment_results(experiment_id)


@router.get("/resilience-report")
def resilience_report(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChaosEngine(db, str(user.id)).get_resilience_report()
