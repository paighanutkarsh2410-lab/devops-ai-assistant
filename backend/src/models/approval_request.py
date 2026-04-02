"""ApprovalRequest model for human-in-the-loop remediation approval."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    action_name = Column(String, nullable=False)
    action_description = Column(String, nullable=True)
    risk_level = Column(String, default="MEDIUM")
    requested_by = Column(String, default="RemediationAgent")
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending")  # pending, approved, rejected, expired
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expiry_minutes = Column(Integer, default=30)
