"""API routes for cost analytics — ROI, allocation, optimization."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from models import get_db
from models.user import User
from utils.auth import get_current_user
from analytics.cost_analyzer import CostAnalyzer

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("/roi")
def roi_summary(
    days: int = Query(30, ge=1, le=365),
    hourly_rate: float = Query(75.0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return CostAnalyzer(db, str(user.id)).roi_summary(days, hourly_rate)


@router.get("/by-service")
def cost_by_service(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return CostAnalyzer(db, str(user.id)).cost_by_service(days)


@router.get("/trend")
def cost_trend(
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return CostAnalyzer(db, str(user.id)).cost_trend(days)


@router.get("/optimizations")
def optimizations(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return CostAnalyzer(db, str(user.id)).optimization_recommendations(days)
