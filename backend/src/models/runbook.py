from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class Runbook(Base):
    __tablename__ = "runbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    incident_pattern = Column(String, nullable=True)  # match keyword
    service_name = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    steps = Column(JSON, nullable=False, default=list)
    estimated_duration_minutes = Column(Integer, nullable=True)
    version = Column(Integer, default=1)
    previous_versions = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="runbooks")


class RunbookExecution(Base):
    __tablename__ = "runbook_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    runbook_id = Column(UUID(as_uuid=True), ForeignKey("runbooks.id"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, default="running")  # running, completed, failed, paused
    current_step = Column(Integer, default=0)
    step_results = Column(JSON, default=list)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    runbook = relationship("Runbook", backref="executions")
