from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from models import get_db
from models.user import User
from models.alert import Alert
from models.predictive_alert import PredictiveAlert
from schemas.alert import AlertCreate, AlertUpdate, AlertResponse
from utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/", response_model=AlertResponse, status_code=201)
def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new alert."""
    alert = Alert(
        user_id=current_user.id,
        incident_id=data.incident_id,
        title=data.title,
        message=data.message,
        severity=data.severity,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    acknowledged: Optional[bool] = Query(None),
    resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List alerts for current user."""
    query = db.query(Alert).filter(Alert.user_id == current_user.id)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.order_by(Alert.triggered_at.desc()).limit(limit).all()


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: str,
    data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge or resolve an alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id, Alert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if data.acknowledged is not None:
        alert.acknowledged = data.acknowledged
        if data.acknowledged:
            alert.acknowledged_at = datetime.utcnow()
    if data.resolved is not None:
        alert.resolved = data.resolved
        if data.resolved:
            alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)
    return alert


# ── Predictive Alerts ───────────────────────────────────────────────────

@router.post("/predictive")
def create_predictive_alert(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new predictive alert."""
    forecasted_date = None
    fd = data.get("forecasted_date")
    if fd:
        try:
            forecasted_date = datetime.fromisoformat(str(fd).replace("Z", ""))
        except (ValueError, TypeError):
            pass

    pa = PredictiveAlert(
        title=data.get("title", "Predicted Issue"),
        message=data.get("message", ""),
        severity=data.get("severity", "low"),
        prediction_type=data.get("prediction_type", "unknown"),
        service_name=data.get("service_name"),
        metric_name=data.get("metric_name"),
        confidence=data.get("confidence", 50),
        forecasted_date=forecasted_date,
        hours_until_issue=data.get("hours_until_issue") or data.get("hours_until_breach"),
        preventive_actions=data.get("preventive_actions"),
    )
    db.add(pa)
    db.commit()
    db.refresh(pa)
    return pa


@router.get("/predictive")
def list_predictive_alerts(
    severity: Optional[str] = None,
    prevented: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List predictive alerts."""
    query = db.query(PredictiveAlert)
    if severity:
        query = query.filter(PredictiveAlert.severity == severity)
    if prevented is not None:
        query = query.filter(PredictiveAlert.prevented == prevented)
    return query.order_by(desc(PredictiveAlert.created_at)).limit(limit).all()


@router.post("/predictive/{alert_id}/prevent")
def mark_prevented(
    alert_id: str,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a predictive alert as prevented."""
    pa = db.query(PredictiveAlert).filter(PredictiveAlert.id == alert_id).first()
    if not pa:
        raise HTTPException(status_code=404, detail="Alert not found")
    pa.prevented = True
    pa.prevention_action = data.get("action_taken", "manual")
    pa.prevented_at = datetime.utcnow()
    db.commit()
    db.refresh(pa)
    return pa


@router.get("/predictive/stats")
def predictive_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get predictive alert statistics."""
    total = db.query(func.count(PredictiveAlert.id)).scalar() or 0
    prevented = db.query(func.count(PredictiveAlert.id)).filter(
        PredictiveAlert.prevented == True
    ).scalar() or 0
    return {
        "total": total,
        "prevented": prevented,
        "prevention_rate": round(prevented / total * 100, 1) if total > 0 else 0,
        "active": total - prevented,
    }
