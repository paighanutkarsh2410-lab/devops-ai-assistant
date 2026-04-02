from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DeploymentCreate(BaseModel):
    service_name: str
    version: str
    commit_hash: Optional[str] = None
    deployed_by: Optional[str] = None
    description: Optional[str] = None


class DeploymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    service_name: str
    version: str
    commit_hash: Optional[str]
    deployed_by: Optional[str]
    description: Optional[str]
    deployed_at: datetime

    class Config:
        from_attributes = True
