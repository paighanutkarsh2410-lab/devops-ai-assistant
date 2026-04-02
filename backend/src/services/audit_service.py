"""Audit service for logging remediation actions."""
from models.database import SessionLocal
from models.action_log import ActionLog
from datetime import datetime


def log_action(action_data: dict) -> dict:
    """Log a complete action."""
    db = SessionLocal()
    try:
        log = ActionLog(**action_data)
        db.add(log)
        db.commit()
        db.refresh(log)
        return {"id": log.id, "status": log.status}
    finally:
        db.close()


def log_action_start(action_data: dict) -> str:
    """Log the start of an action. Returns action_id."""
    action_data["status"] = "in_progress"
    action_data["executed_at"] = datetime.utcnow()
    result = log_action(action_data)
    return result["id"]


def log_action_complete(action_id: str, result: dict):
    """Update an action log with completion data."""
    db = SessionLocal()
    try:
        log = db.query(ActionLog).filter(ActionLog.id == action_id).first()
        if log:
            log.status = result.get("status", "success")
            log.duration_seconds = result.get("duration_seconds", 0)
            log.impact_score = result.get("impact_score", 0)
            log.after_state = result.get("after_state")
            log.error_message = result.get("error_message")
            log.rollback_performed = result.get("rollback_performed", False)
            db.commit()
    finally:
        db.close()


def log_rollback(action_id: str, reason: str):
    """Mark an action as rolled back."""
    db = SessionLocal()
    try:
        log = db.query(ActionLog).filter(ActionLog.id == action_id).first()
        if log:
            log.status = "rollback"
            log.rollback_performed = True
            log.error_message = reason
            db.commit()
    finally:
        db.close()
