"""NotificationPreference model for user notification settings."""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    channel = Column(String, nullable=False)  # slack, email, sms
    enabled = Column(Boolean, default=True)
    severity_threshold = Column(String, default="low")  # only notify at this level and above
    services = Column(JSON, default=[])  # subscribe to specific services, empty = all
    quiet_hours_start = Column(Integer, nullable=True)  # hour (0-23)
    quiet_hours_end = Column(Integer, nullable=True)
    digest_frequency = Column(String, default="daily")  # daily, weekly
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OnCallSchedule(Base):
    __tablename__ = "on_call_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_hour = Column(Integer, default=0)
    end_hour = Column(Integer, default=24)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
