from pydantic import BaseModel
from typing import Optional, List


class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str  # detection, alert, metric_spike, deployment, error_log, diagnosis, resolution
    description: str
    metadata: Optional[dict] = None


class TimelineResponse(BaseModel):
    incident_id: str
    events: List[TimelineEvent]
    summary: Optional[str] = None
