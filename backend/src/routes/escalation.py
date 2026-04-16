"""API routes for escalation policies, on-call, and manual escalation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from models import get_db
from models.user import User
from models.escalation_policy import EscalationPolicy, OnCallRotation
from utils.auth import get_current_user
from services.escalation_service import EscalationService

router = APIRouter(prefix="/escalation", tags=["escalation"])


class PolicyCreate(BaseModel):
    name: str
    service_name: Optional[str] = None
    severity_levels: list = []
    levels: list = []
    enabled: bool = True


class OnCallCreate(BaseModel):
    name: str
    rotation_type: str = "weekly"
    participants: list = []
    timezone: str = "UTC"


# ── Policies ────────────────────────────────────────────────────────────

@router.post("/policies", status_code=201)
def create_policy(
    body: PolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    policy = EscalationPolicy(
        user_id=user.id,
        name=body.name,
        service_name=body.service_name,
        severity_levels=body.severity_levels,
        levels=body.levels,
        enabled=body.enabled,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return _serialize_policy(policy)


@router.get("/policies")
def list_policies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    policies = db.query(EscalationPolicy).filter(
        EscalationPolicy.user_id == user.id
    ).order_by(EscalationPolicy.created_at.desc()).all()
    return [_serialize_policy(p) for p in policies]


@router.delete("/policies/{policy_id}", status_code=204)
def delete_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    policy = db.query(EscalationPolicy).filter(
        EscalationPolicy.id == policy_id, EscalationPolicy.user_id == user.id
    ).first()
    if not policy:
        raise HTTPException(404, "Policy not found")
    db.delete(policy)
    db.commit()


# ── On-Call ─────────────────────────────────────────────────────────────

@router.get("/on-call")
def get_on_call(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return EscalationService(db, str(user.id)).get_on_call()


@router.post("/on-call", status_code=201)
def create_on_call(
    body: OnCallCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = OnCallRotation(
        user_id=user.id,
        name=body.name,
        rotation_type=body.rotation_type,
        participants=body.participants,
        timezone=body.timezone,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return {
        "id": str(schedule.id),
        "name": schedule.name,
        "rotation_type": schedule.rotation_type,
        "participants": schedule.participants,
    }


# ── Escalation actions ─────────────────────────────────────────────────

@router.post("/incidents/{incident_id}/escalate")
def escalate_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return EscalationService(db, str(user.id)).start_escalation(incident_id)


@router.post("/incidents/{incident_id}/acknowledge")
def acknowledge_escalation(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return EscalationService(db, str(user.id)).acknowledge_escalation(incident_id)


@router.get("/incidents/{incident_id}/status")
def escalation_status(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return EscalationService(db, str(user.id)).check_escalation_needed(incident_id)


@router.post("/incidents/{incident_id}/next-level")
def escalate_next_level(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return EscalationService(db, str(user.id)).escalate_to_next_level(incident_id)


# ── Analytics ───────────────────────────────────────────────────────────

@router.get("/analytics")
def escalation_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return EscalationService(db, str(user.id)).get_escalation_analytics()


def _serialize_policy(p: EscalationPolicy) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "service_name": p.service_name,
        "severity_levels": p.severity_levels,
        "levels": p.levels,
        "enabled": p.enabled,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
