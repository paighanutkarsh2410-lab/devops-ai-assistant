from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)

    # Alert info
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # critical, warning, info

    # Status
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)

    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Additional data
    extra_data = Column("metadata", JSON, nullable=True)

    # Relationships
    user = relationship("User", backref="alerts")
    incident = relationship("Incident", backref="alerts")

    def __repr__(self):
        return f"<Alert {self.title} - {self.severity}>"
