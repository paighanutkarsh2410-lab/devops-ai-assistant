"""API routes for trend analysis — regime changes, cyclical patterns, anomalies."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from models import get_db
from models.user import User
from utils.auth import get_current_user
from analytics.trend_analyzer import TrendAnalyzer

router = APIRouter(prefix="/trends", tags=["trends"])


def _analyzer(db: Session, user: User) -> TrendAnalyzer:
    return TrendAnalyzer(db, str(user.id))


@router.get("/summary")
def trend_summary(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _analyzer(db, user).trend_summary(days)


@router.get("/severity")
def severity_trends(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _analyzer(db, user).severity_trends(days)


@router.get("/services")
def service_trends(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _analyzer(db, user).service_trends(days)


@router.get("/resolution")
def resolution_trends(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _analyzer(db, user).resolution_trends(days)


@router.get("/anomalies")
def anomaly_detection(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _analyzer(db, user).anomaly_detection(days)
