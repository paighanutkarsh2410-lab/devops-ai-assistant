"""Audit routes for viewing remediation action logs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.action_log import ActionLog
from schemas.action_log import ActionLogCreate, ActionLogResponse, ActionStats

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/actions", response_model=ActionLogResponse)
def log_action(entry: ActionLogCreate, db: Session = Depends(get_db)):
    """Log a remediation action."""
    log = ActionLog(**entry.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/actions", response_model=list[ActionLogResponse])
def list_actions(status: str = None, action_name: str = None,
                 limit: int = 50, skip: int = 0,
                 db: Session = Depends(get_db)):
    """List all action logs with optional filters."""
    query = db.query(ActionLog)
    if status:
        query = query.filter(ActionLog.status == status)
    if action_name:
        query = query.filter(ActionLog.action_name == action_name)
    return query.order_by(ActionLog.executed_at.desc()).offset(skip).limit(limit).all()


@router.get("/actions/{action_id}", response_model=ActionLogResponse)
def get_action(action_id: str, db: Session = Depends(get_db)):
    """Get details of a specific action."""
    log = db.query(ActionLog).filter(ActionLog.id == action_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Action log not found")
    return log


@router.get("/incidents/{incident_id}/actions", response_model=list[ActionLogResponse])
def get_incident_actions(incident_id: str, db: Session = Depends(get_db)):
    """Get all actions taken for an incident."""
    return db.query(ActionLog).filter(
        ActionLog.incident_id == incident_id
    ).order_by(ActionLog.executed_at.desc()).all()


@router.get("/services/{service_name}/actions", response_model=list[ActionLogResponse])
def get_service_actions(service_name: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get actions taken on a specific service (via incident)."""
    return db.query(ActionLog).filter(
        ActionLog.incident_id.isnot(None)
    ).order_by(ActionLog.executed_at.desc()).limit(limit).all()


@router.get("/stats", response_model=ActionStats)
def get_stats(db: Session = Depends(get_db)):
    """Get aggregate action statistics."""
    total = db.query(func.count(ActionLog.id)).scalar() or 0
    success = db.query(func.count(ActionLog.id)).filter(ActionLog.status == "success").scalar() or 0
    failure = db.query(func.count(ActionLog.id)).filter(ActionLog.status == "failure").scalar() or 0
    rollback = db.query(func.count(ActionLog.id)).filter(ActionLog.status == "rollback").scalar() or 0
    avg_dur = db.query(func.avg(ActionLog.duration_seconds)).scalar() or 0
    avg_impact = db.query(func.avg(ActionLog.impact_score)).scalar() or 0

    return ActionStats(
        total_actions=total,
        success_count=success,
        failure_count=failure,
        rollback_count=rollback,
        success_rate=round((success / total * 100) if total > 0 else 0, 1),
        avg_duration=round(float(avg_dur), 2),
        avg_impact=round(float(avg_impact), 1),
    )
