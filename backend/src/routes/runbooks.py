"""API routes for runbook management and execution."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from models import get_db
from models.user import User
from models.runbook import Runbook
from utils.auth import get_current_user
from services.runbook_executor import RunbookExecutor

router = APIRouter(prefix="/runbooks", tags=["runbooks"])


class RunbookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    incident_pattern: Optional[str] = None
    service_name: Optional[str] = None
    severity: Optional[str] = None
    steps: list = []
    estimated_duration_minutes: Optional[int] = None
    tags: list = []


class RunbookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    incident_pattern: Optional[str] = None
    steps: Optional[list] = None
    tags: Optional[list] = None


@router.post("/", status_code=201)
def create_runbook(
    body: RunbookCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rb = Runbook(
        user_id=user.id,
        name=body.name,
        description=body.description,
        incident_pattern=body.incident_pattern,
        service_name=body.service_name,
        severity=body.severity,
        steps=body.steps,
        estimated_duration_minutes=body.estimated_duration_minutes,
        tags=body.tags,
    )
    db.add(rb)
    db.commit()
    db.refresh(rb)
    return _serialize(rb)


@router.get("/")
def list_runbooks(
    service_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Runbook).filter(Runbook.user_id == user.id)
    if service_name:
        q = q.filter(Runbook.service_name == service_name)
    return [_serialize(rb) for rb in q.order_by(Runbook.updated_at.desc()).all()]


@router.get("/library")
def runbook_library():
    """Pre-built runbook templates."""
    return [
        {
            "name": "Database Connection Pool Exhaustion",
            "description": "Investigate and resolve DB connection pool issues",
            "incident_pattern": "connection pool",
            "service_name": "database",
            "tags": ["database", "connections", "pool"],
            "estimated_duration_minutes": 20,
            "steps": [
                {"order": 1, "type": "automated", "name": "Check connections", "action": "analyze_connections", "params": {"service": "database"}},
                {"order": 2, "type": "automated", "name": "Collect DB logs", "action": "collect_logs", "params": {"service": "database", "duration": "10m"}},
                {"order": 3, "type": "manual", "name": "Review connection patterns", "instruction": "Check for connection leaks in application code"},
                {"order": 4, "type": "automated", "name": "Restart service", "action": "restart_service", "params": {"service": "database"}, "requires_approval": True},
                {"order": 5, "type": "automated", "name": "Verify recovery", "action": "run_health_check", "params": {"service": "database"}},
            ],
        },
        {
            "name": "Memory Leak Investigation",
            "description": "Diagnose and fix memory leak issues",
            "incident_pattern": "memory",
            "tags": ["memory", "leak", "oom"],
            "estimated_duration_minutes": 30,
            "steps": [
                {"order": 1, "type": "automated", "name": "Check metrics", "action": "check_metrics", "params": {"metric": "memory_usage"}},
                {"order": 2, "type": "automated", "name": "Collect logs", "action": "collect_logs", "params": {"duration": "30m"}},
                {"order": 3, "type": "manual", "name": "Analyze heap dumps", "instruction": "Review memory allocation patterns and identify leaking objects"},
                {"order": 4, "type": "automated", "name": "Restart service", "action": "restart_service", "params": {}},
                {"order": 5, "type": "manual", "name": "Create fix ticket", "instruction": "File a ticket for the root cause fix"},
            ],
        },
        {
            "name": "API Timeout Debugging",
            "description": "Debug and resolve API timeout issues",
            "incident_pattern": "timeout",
            "service_name": "api-server",
            "tags": ["timeout", "latency", "api"],
            "estimated_duration_minutes": 15,
            "steps": [
                {"order": 1, "type": "automated", "name": "Check metrics", "action": "check_metrics", "params": {"metric": "response_time"}},
                {"order": 2, "type": "automated", "name": "Collect logs", "action": "collect_logs", "params": {"service": "api-server", "duration": "5m"}},
                {"order": 3, "type": "manual", "name": "Identify slow endpoints", "instruction": "Find the slowest endpoints from logs"},
                {"order": 4, "type": "automated", "name": "Scale up", "action": "scale_up", "params": {"service": "api-server"}},
            ],
        },
        {
            "name": "Disk Full Remediation",
            "description": "Free disk space and prevent recurrence",
            "incident_pattern": "disk",
            "tags": ["disk", "storage", "full"],
            "estimated_duration_minutes": 10,
            "steps": [
                {"order": 1, "type": "automated", "name": "Check disk space", "action": "check_disk_space", "params": {}},
                {"order": 2, "type": "automated", "name": "Clear old logs", "action": "clear_cache", "params": {"target": "logs"}},
                {"order": 3, "type": "manual", "name": "Review large files", "instruction": "Identify and remove unnecessary large files"},
                {"order": 4, "type": "automated", "name": "Verify space", "action": "check_disk_space", "params": {}},
            ],
        },
        {
            "name": "Certificate Expiration",
            "description": "Renew expired or expiring TLS certificates",
            "incident_pattern": "certificate",
            "tags": ["ssl", "tls", "certificate", "expiry"],
            "estimated_duration_minutes": 15,
            "steps": [
                {"order": 1, "type": "manual", "name": "Check certificate status", "instruction": "Verify which certificates are expired or expiring"},
                {"order": 2, "type": "automated", "name": "Rotate credentials", "action": "rotate_credentials", "params": {"type": "tls"}},
                {"order": 3, "type": "automated", "name": "Restart services", "action": "restart_service", "params": {}},
                {"order": 4, "type": "automated", "name": "Health check", "action": "run_health_check", "params": {}},
            ],
        },
    ]


@router.get("/{runbook_id}")
def get_runbook(
    runbook_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rb = _get_owned(db, user, runbook_id)
    return _serialize(rb)


@router.put("/{runbook_id}")
def update_runbook(
    runbook_id: str,
    body: RunbookUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rb = _get_owned(db, user, runbook_id)
    # Save previous version
    prev = rb.previous_versions or []
    prev.append({"version": rb.version, "steps": rb.steps, "updated_at": rb.updated_at.isoformat() if rb.updated_at else None})
    rb.previous_versions = prev
    rb.version = (rb.version or 1) + 1

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(rb, field, val)
    rb.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rb)
    return _serialize(rb)


@router.delete("/{runbook_id}", status_code=204)
def delete_runbook(
    runbook_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rb = _get_owned(db, user, runbook_id)
    db.delete(rb)
    db.commit()


@router.post("/{runbook_id}/execute")
def execute_runbook(
    runbook_id: str,
    incident_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return RunbookExecutor(db, str(user.id)).execute_runbook(runbook_id, incident_id)


@router.get("/{runbook_id}/executions")
def get_executions(
    runbook_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return RunbookExecutor(db, str(user.id)).get_executions(runbook_id, limit)


@router.get("/suggest/{incident_id}")
def suggest_runbook(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return RunbookExecutor(db, str(user.id)).suggest_runbook(incident_id)


@router.get("/analytics/stats")
def runbook_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return RunbookExecutor(db, str(user.id)).get_analytics()


def _get_owned(db, user, runbook_id):
    rb = db.query(Runbook).filter(Runbook.id == runbook_id, Runbook.user_id == user.id).first()
    if not rb:
        raise HTTPException(404, "Runbook not found")
    return rb


def _serialize(rb: Runbook) -> dict:
    return {
        "id": str(rb.id),
        "name": rb.name,
        "description": rb.description,
        "incident_pattern": rb.incident_pattern,
        "service_name": rb.service_name,
        "severity": rb.severity,
        "steps": rb.steps,
        "estimated_duration_minutes": rb.estimated_duration_minutes,
        "version": rb.version,
        "tags": rb.tags,
        "created_at": rb.created_at.isoformat() if rb.created_at else None,
        "updated_at": rb.updated_at.isoformat() if rb.updated_at else None,
    }
