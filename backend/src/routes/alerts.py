from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import get_db
from models.user import User
from models.alert import Alert
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
