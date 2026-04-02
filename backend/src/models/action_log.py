"""ActionLog model for audit trail of all remediation actions."""
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(String, nullable=True)
    action_name = Column(String, nullable=False)
    action_type = Column(String, default="remediation")  # remediation, diagnostic, manual
    executed_by = Column(String, default="system")
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_seconds = Column(Float, default=0)
    status = Column(String, default="success")  # success, failure, rollback
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    impact_score = Column(Float, default=0)
    rollback_performed = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)
