from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str  # critical, high, medium, low
    service_name: Optional[str] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IncidentResponse(IncidentBase):
    id: UUID
    user_id: UUID
    status: str
    root_cause: Optional[str]
    solution: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]
    auto_resolved: bool
    resolution_time_seconds: Optional[int]

    class Config:
        from_attributes = True
