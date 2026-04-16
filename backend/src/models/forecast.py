"""Forecast model for storing prediction results."""
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    forecast_type = Column(String, default="metric")  # metric, capacity, cost
    horizon_hours = Column(Integer, default=24)
    method = Column(String, default="linear_regression")  # prophet, linear_regression
    forecast_data = Column(JSON, nullable=True)  # forecast points
    trend_direction = Column(String, nullable=True)  # increasing, decreasing, stable
    breach_predicted = Column(Boolean, default=False)
    hours_until_breach = Column(Float, nullable=True)
    confidence = Column(Float, default=50.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CapacityPlan(Base):
    __tablename__ = "capacity_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String, nullable=False)
    plan_type = Column(String, default="auto")  # auto, event, manual
    event_name = Column(String, nullable=True)
    current_utilization = Column(Float, default=0)
    predicted_utilization = Column(Float, default=0)
    recommendation = Column(String, nullable=True)
    additional_instances = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0)
    plan_data = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, approved, executed, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CostForecast(Base):
    __tablename__ = "cost_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period = Column(String, nullable=False)  # 2024-01, 2024-02
    forecast_type = Column(String, default="monthly")
    current_cost = Column(Float, default=0)
    predicted_cost = Column(Float, default=0)
    cost_breakdown = Column(JSON, nullable=True)
    optimizations = Column(JSON, nullable=True)
    accuracy = Column(Float, nullable=True)  # compared to actual after period ends
    created_at = Column(DateTime(timezone=True), server_default=func.now())
