"""PredictiveAlert model for prediction-based alerts."""
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class PredictiveAlert(Base):
    __tablename__ = "predictive_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    message = Column(String, nullable=True)
    severity = Column(String, default="low")  # critical, high, medium, low
    prediction_type = Column(String, nullable=False)  # resource_exhaustion, capacity_breach, etc.
    service_name = Column(String, nullable=True)
    metric_name = Column(String, nullable=True)
    confidence = Column(Float, default=50.0)
    forecasted_date = Column(DateTime(timezone=True), nullable=True)
    hours_until_issue = Column(Float, nullable=True)
    prevented = Column(Boolean, default=False)
    prevention_action = Column(String, nullable=True)
    prevented_at = Column(DateTime(timezone=True), nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
