"""Incident assignment tracking."""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class IncidentAssignment(Base):
    __tablename__ = "incident_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String, default="assigned")  # assigned, in_progress, resolved
    assigned_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="assignments")
    incident = relationship("Incident", backref="assignments")

    def __repr__(self):
        return f"<Assignment {self.user_id} → {self.incident_id}>"
