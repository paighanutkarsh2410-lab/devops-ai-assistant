"""Pydantic schemas for action logs (audit trail)."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ActionLogCreate(BaseModel):
    incident_id: Optional[str] = None
    action_name: str
    action_type: str = "remediation"
    executed_by: str = "system"
    duration_seconds: float = 0
    status: str = "success"
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    impact_score: float = 0
    rollback_performed: bool = False
    error_message: Optional[str] = None
    approval_required: bool = False
    approved_by: Optional[str] = None


class ActionLogResponse(BaseModel):
    id: str
    incident_id: Optional[str] = None
    action_name: str
    action_type: str
    executed_by: str
    executed_at: datetime
    duration_seconds: float
    status: str
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    impact_score: float
    rollback_performed: bool
    error_message: Optional[str] = None
    approval_required: bool
    approved_by: Optional[str] = None

    class Config:
        from_attributes = True


class ActionStats(BaseModel):
    total_actions: int
    success_count: int
    failure_count: int
    rollback_count: int
    success_rate: float
    avg_duration: float
    avg_impact: float
