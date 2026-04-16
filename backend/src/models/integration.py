from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # jira, slack, pagerduty, datadog, etc.
    integration_type = Column(String, nullable=False)  # ticketing, notification, monitoring, scm
    config = Column(JSON, nullable=False, default=dict)  # encrypted API keys, URLs
    enabled = Column(Boolean, default=True)
    last_synced = Column(DateTime, nullable=True)
    sync_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="integrations")
