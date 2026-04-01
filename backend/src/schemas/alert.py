from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str  # critical, warning, info
    incident_id: Optional[UUID] = None


class AlertUpdate(BaseModel):
    acknowledged: Optional[bool] = None
    resolved: Optional[bool] = None


class AlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    incident_id: Optional[UUID]
    title: str
    message: str
    severity: str
    acknowledged: bool
    resolved: bool
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
