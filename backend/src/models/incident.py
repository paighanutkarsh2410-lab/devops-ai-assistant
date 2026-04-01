from sqlalchemy import Column, String, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic info
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    severity = Column(String, nullable=False)  # critical, high, medium, low
    status = Column(String, nullable=False)  # open, investigating, resolved, closed

    # Technical details
    service_name = Column(String, nullable=True)
    root_cause = Column(String, nullable=True)
    solution = Column(String, nullable=True)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Metadata
    extra_data = Column("metadata", JSON, nullable=True)

    # Auto-resolution tracking
    auto_resolved = Column(Boolean, default=False)
    resolution_time_seconds = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", backref="incidents")

    def __repr__(self):
        return f"<Incident {self.title} - {self.status}>"
