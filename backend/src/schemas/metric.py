from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    timestamp: Optional[datetime] = None


class MetricBulkCreate(BaseModel):
    metrics: List[MetricCreate]


class MetricResponse(BaseModel):
    id: UUID
    user_id: UUID
    service_name: str
    metric_name: str
    value: float
    unit: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricAggregation(BaseModel):
    avg: float
    min: float
    max: float
    count: int
