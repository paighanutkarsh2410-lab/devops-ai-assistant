"""LearningData model for storing learned patterns and action success rates."""
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class LearningData(Base):
    __tablename__ = "learning_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_type = Column(String, nullable=False)  # memory_leak, cpu_spike, api_timeout, etc.
    service_name = Column(String, nullable=True)
    action_name = Column(String, nullable=True)
    frequency = Column(Integer, default=1)
    success_rate = Column(Float, default=0.0)
    total_attempts = Column(Integer, default=0)
    total_successes = Column(Integer, default=0)
    avg_resolution_time = Column(Float, default=0.0)  # seconds
    confidence = Column(Float, default=0.0)
    symptoms = Column(JSON, nullable=True)  # list of symptom patterns
    root_causes = Column(JSON, nullable=True)  # linked root causes
    solutions = Column(JSON, nullable=True)  # linked solutions
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
