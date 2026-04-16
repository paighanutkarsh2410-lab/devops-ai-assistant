"""NotificationLog model for tracking all notifications sent."""
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False)
    channel = Column(String, nullable=False)  # slack, email, sms
    recipient = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    title = Column(String, nullable=True)
    status = Column(String, default="sent")  # sent, failed, suppressed, buffered
    read = Column(Boolean, default=False)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
