"""Pattern model for discovered incident patterns."""
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # e.g., "Memory Leak Pattern"
    description = Column(String, nullable=True)
    pattern_type = Column(String, nullable=False)  # memory_leak, cpu_spike, etc.
    frequency = Column(Integer, default=1)
    confidence = Column(Float, default=0.0)
    symptoms = Column(JSON, nullable=True)  # metric spikes, error messages, etc.
    common_root_causes = Column(JSON, nullable=True)
    best_actions = Column(JSON, nullable=True)  # ranked action list
    affected_services = Column(JSON, nullable=True)
    time_distribution = Column(JSON, nullable=True)  # hour/day patterns
    trending = Column(String, default="stable")  # increasing, decreasing, stable
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
