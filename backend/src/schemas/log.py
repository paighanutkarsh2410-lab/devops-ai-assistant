from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class LogCreate(BaseModel):
    service_name: str
    level: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    timestamp: Optional[datetime] = None


class LogBulkCreate(BaseModel):
    logs: List[LogCreate]


class LogResponse(BaseModel):
    id: UUID
    user_id: UUID
    service_name: str
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ErrorPattern(BaseModel):
    pattern: str
    count: int
    level: str
