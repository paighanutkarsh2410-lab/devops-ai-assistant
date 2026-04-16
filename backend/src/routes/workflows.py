"""API routes for custom workflow builder."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from models import get_db
from models.user import User
from models.workflow import Workflow, WorkflowExecution
from utils.auth import get_current_user
from services.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_conditions: dict = {}
    steps: list = []
    enabled: bool = True


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_conditions: Optional[dict] = None
    steps: Optional[list] = None
    enabled: Optional[bool] = None


class WorkflowExecuteRequest(BaseModel):
    context: dict = {}
    trigger_type: str = "manual"


@router.post("/", status_code=201)
def create_workflow(
    body: WorkflowCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = Workflow(
        user_id=user.id,
        name=body.name,
        description=body.description,
        trigger_conditions=body.trigger_conditions,
        steps=body.steps,
        enabled=body.enabled,
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return _serialize(wf)


@router.get("/")
def list_workflows(
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Workflow).filter(Workflow.user_id == user.id)
    if enabled is not None:
        q = q.filter(Workflow.enabled == enabled)
    workflows = q.order_by(Workflow.updated_at.desc()).all()
    return [_serialize(w) for w in workflows]


@router.get("/templates")
def workflow_templates():
    """Pre-built workflow templates."""
    return [
        {
            "name": "Critical Incident Response",
            "description": "Auto-diagnose, notify, and escalate critical incidents",
            "trigger_conditions": {"type": "incident_created", "filters": {"severity": "critical"}},
            "steps": [
                {"type": "send_notification", "name": "Alert Team", "params": {"channels": ["slack"], "message": "Critical incident detected!"}},
                {"type": "run_diagnostic", "name": "Auto Diagnose", "params": {}},
                {"type": "conditional", "name": "Check Root Cause", "params": {"condition": "has_root_cause", "true_step": 3, "false_step": 4}},
                {"type": "execute_action", "name": "Auto Remediate", "params": {"action": "restart_service"}},
                {"type": "create_ticket", "name": "Create Jira Ticket", "params": {"system": "jira", "title": "Critical incident needs investigation"}},
            ],
        },
        {
            "name": "Prediction-Based Scaling",
            "description": "Scale services when prediction alerts fire",
            "trigger_conditions": {"type": "prediction_alert", "filters": {}},
            "steps": [
                {"type": "log", "name": "Log Prediction", "params": {"message": "Prediction alert received", "level": "info"}},
                {"type": "execute_action", "name": "Scale Up", "params": {"action": "scale_up", "target": "auto"}},
                {"type": "delay", "name": "Wait 5 min", "params": {"seconds": 300}},
                {"type": "send_notification", "name": "Notify", "params": {"channels": ["slack"], "message": "Preventive scaling completed"}},
            ],
        },
        {
            "name": "Weekly Maintenance",
            "description": "Automated weekly maintenance tasks",
            "trigger_conditions": {"type": "schedule", "filters": {"cron": "0 2 * * 0"}},
            "steps": [
                {"type": "send_notification", "name": "Start Notice", "params": {"channels": ["slack"], "message": "Weekly maintenance starting"}},
                {"type": "execute_action", "name": "Clear Cache", "params": {"action": "clear_cache"}},
                {"type": "execute_action", "name": "Rotate Logs", "params": {"action": "rotate_logs"}},
                {"type": "api_call", "name": "Health Check", "params": {"url": "/health", "method": "GET"}},
                {"type": "send_notification", "name": "Complete Notice", "params": {"channels": ["slack"], "message": "Weekly maintenance complete"}},
            ],
        },
        {
            "name": "Cost Optimization",
            "description": "Scale down underutilized services during off-hours",
            "trigger_conditions": {"type": "schedule", "filters": {"cron": "0 22 * * *"}},
            "steps": [
                {"type": "log", "name": "Start Optimization", "params": {"message": "Running cost optimization", "level": "info"}},
                {"type": "execute_action", "name": "Scale Down", "params": {"action": "scale_down", "target": "non-critical"}},
                {"type": "send_notification", "name": "Report", "params": {"channels": ["email"], "message": "Nightly cost optimization complete"}},
            ],
        },
        {
            "name": "Security Incident Response",
            "description": "Immediate response to security-related incidents",
            "trigger_conditions": {"type": "incident_created", "filters": {"severity": "critical"}},
            "steps": [
                {"type": "send_notification", "name": "Alert Security Team", "params": {"channels": ["slack", "email"], "message": "SECURITY INCIDENT DETECTED"}},
                {"type": "execute_action", "name": "Enable Rate Limiting", "params": {"action": "rate_limit"}},
                {"type": "wait_for_approval", "name": "Await Approval", "params": {"approver": "security_lead", "auto_approve": False}},
                {"type": "execute_action", "name": "Block IPs", "params": {"action": "block_suspicious_ips"}},
                {"type": "create_ticket", "name": "Create Security Ticket", "params": {"system": "jira", "title": "Security incident investigation"}},
            ],
        },
    ]


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = _get_owned(db, user, workflow_id)
    return _serialize(wf)


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = _get_owned(db, user, workflow_id)
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(wf, field, val)
    wf.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(wf)
    return _serialize(wf)


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = _get_owned(db, user, workflow_id)
    db.delete(wf)
    db.commit()


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: str,
    body: WorkflowExecuteRequest = WorkflowExecuteRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    engine = WorkflowEngine(db, str(user.id))
    return engine.execute_workflow(workflow_id, body.context, body.trigger_type)


@router.get("/{workflow_id}/executions")
def get_executions(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    engine = WorkflowEngine(db, str(user.id))
    return engine.get_executions(workflow_id, limit)


# ── Helpers ─────────────────────────────────────────────────────────────

def _get_owned(db: Session, user: User, workflow_id: str) -> Workflow:
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id, Workflow.user_id == user.id
    ).first()
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return wf


def _serialize(wf: Workflow) -> dict:
    return {
        "id": str(wf.id),
        "name": wf.name,
        "description": wf.description,
        "trigger_conditions": wf.trigger_conditions,
        "steps": wf.steps,
        "enabled": wf.enabled,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
        "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
    }
