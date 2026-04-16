"""ActionOutcome model for tracking remediation action results over time."""
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class ActionOutcome(Base):
    __tablename__ = "action_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(String, nullable=True)
    action_name = Column(String, nullable=False)
    incident_pattern = Column(String, nullable=True)  # pattern type
    service_name = Column(String, nullable=True)
    success = Column(Boolean, default=False)
    duration_seconds = Column(Float, default=0.0)
    impact_score = Column(Float, default=0.0)
    was_recommended = Column(Boolean, default=False)
    recommendation_rank = Column(Integer, nullable=True)  # 1=top recommendation
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
