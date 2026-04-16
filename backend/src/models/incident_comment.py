"""Incident comments for collaborative investigation."""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    edited_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="comments")
    incident = relationship("Incident", backref="comments")

    def __repr__(self):
        return f"<Comment {self.id} on {self.incident_id}>"
