"""Pydantic schemas for approval requests."""
from pydantic import BaseModel, field_validator
from typing import Optional, Any
from datetime import datetime


class ApprovalCreate(BaseModel):
    incident_id: str
    action_name: str
    action_description: Optional[str] = None
    risk_level: str = "MEDIUM"


class ApprovalResponse(BaseModel):
    id: str
    incident_id: str
    action_name: str
    action_description: Optional[str] = None
    risk_level: str
    requested_by: str
    requested_at: datetime
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    expiry_minutes: int

    @field_validator("id", "incident_id", mode="before")
    @classmethod
    def stringify_uuid(cls, v: Any) -> str:
        return str(v) if v is not None else v

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    """Schema for approve/reject actions."""
    reason: Optional[str] = None
