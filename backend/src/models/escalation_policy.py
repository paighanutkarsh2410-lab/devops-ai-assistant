from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    service_name = Column(String, nullable=True)  # null = all services
    severity_levels = Column(JSON, default=list)  # which severities this applies to
    levels = Column(JSON, nullable=False, default=list)  # escalation levels array
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="escalation_policies")


class EscalationRecord(Base):
    __tablename__ = "escalation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("escalation_policies.id"), nullable=True)
    current_level = Column(Integer, default=1)
    status = Column(String, default="active")  # active, acknowledged, resolved, cancelled
    notified_contacts = Column(JSON, default=list)
    escalation_history = Column(JSON, default=list)
    started_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    next_escalation_at = Column(DateTime, nullable=True)

    incident = relationship("Incident", backref="escalation_records")


class OnCallRotation(Base):
    __tablename__ = "on_call_rotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    rotation_type = Column(String, default="weekly")  # weekly, daily, custom
    participants = Column(JSON, nullable=False, default=list)  # list of {name, email, phone}
    current_index = Column(Integer, default=0)
    overrides = Column(JSON, default=list)  # temporary overrides
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_rel = relationship("User", backref="on_call_rotations")
