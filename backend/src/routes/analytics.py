"""API routes for advanced analytics — MTTR, MTTD, MTBF, reliability, cost impact."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from models import get_db
from models.user import User
from utils.auth import get_current_user
from analytics.analytics_engine import AnalyticsEngine

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _engine(db: Session, user: User) -> AnalyticsEngine:
    return AnalyticsEngine(db, str(user.id))


# ── MTTR ────────────────────────────────────────────────────────────────

@router.get("/mttr")
def get_mttr(
    days: int = Query(30, ge=1, le=365),
    severity: Optional[str] = None,
    service_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    date_from = datetime.utcnow() - timedelta(days=days)
    filters = {}
    if severity:
        filters["severity"] = severity
    if service_name:
        filters["service_name"] = service_name
    return _engine(db, user).calculate_mttr(date_from=date_from, filters=filters)


# ── MTTD ────────────────────────────────────────────────────────────────

@router.get("/mttd")
def get_mttd(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    date_from = datetime.utcnow() - timedelta(days=days)
    return _engine(db, user).calculate_mttd(date_from=date_from)


# ── MTBF ────────────────────────────────────────────────────────────────

@router.get("/mtbf/{service_name}")
def get_mtbf(
    service_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).calculate_mtbf(service_name)


# ── Incident frequency ──────────────────────────────────────────────────

@router.get("/frequency")
def get_frequency(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).incident_frequency_analysis(days)


# ── Root cause distribution ─────────────────────────────────────────────

@router.get("/root-causes")
def get_root_causes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).root_cause_distribution()


# ── Service reliability ─────────────────────────────────────────────────

@router.get("/reliability")
def get_reliability(
    service_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).service_reliability_score(service_name)


# ── Blast radius ────────────────────────────────────────────────────────

@router.get("/blast-radius/{incident_id}")
def get_blast_radius(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).calculate_blast_radius(incident_id)


# ── Effectiveness ───────────────────────────────────────────────────────

@router.get("/effectiveness")
def get_effectiveness(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).effectiveness_metrics()


# ── Cost impact ─────────────────────────────────────────────────────────

@router.get("/cost-impact")
def get_cost_impact(
    hourly_rate: float = Query(75.0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _engine(db, user).cost_impact_analysis(hourly_rate)


# ── Dashboard summary ──────────────────────────────────────────────────

@router.get("/dashboard")
def analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """All key analytics in one call for the dashboard."""
    eng = _engine(db, user)
    date_from = datetime.utcnow() - timedelta(days=days)
    return {
        "mttr": eng.calculate_mttr(date_from=date_from),
        "mttd": eng.calculate_mttd(date_from=date_from),
        "frequency": eng.incident_frequency_analysis(days),
        "root_causes": eng.root_cause_distribution(),
        "reliability": eng.service_reliability_score(),
        "effectiveness": eng.effectiveness_metrics(),
        "cost_impact": eng.cost_impact_analysis(),
    }
