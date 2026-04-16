from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class SLAConfig(Base):
    __tablename__ = "sla_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    service_name = Column(String, nullable=False)
    target_uptime = Column(Float, nullable=False, default=99.9)  # percentage
    max_mttr_minutes = Column(Integer, nullable=False, default=30)
    max_incidents_per_month = Column(Integer, nullable=True)
    error_budget_minutes = Column(Float, nullable=False, default=43.2)  # 99.9% = 43.2 min/month
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="sla_configs")


class SLARecord(Base):
    __tablename__ = "sla_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    service_name = Column(String, nullable=False)
    period = Column(String, nullable=False)  # "2026-04" (monthly)
    uptime_percent = Column(Float, nullable=False)
    total_downtime_minutes = Column(Float, nullable=False, default=0)
    error_budget_remaining = Column(Float, nullable=False)
    incidents_count = Column(Integer, default=0)
    avg_mttr_minutes = Column(Float, nullable=True)
    sla_met = Column(Boolean, default=True)
    breaches = Column(JSON, default=list)  # list of breach events
    calculated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="sla_records")
