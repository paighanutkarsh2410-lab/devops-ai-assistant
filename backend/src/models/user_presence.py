"""User presence tracking for collaborative features."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class UserPresence(Base):
    __tablename__ = "user_presence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    current_page = Column(String, nullable=True)
    current_incident_id = Column(String, nullable=True)

    user = relationship("User", backref="presence")

    def __repr__(self):
        return f"<Presence {self.user_id} online={self.is_online}>"
