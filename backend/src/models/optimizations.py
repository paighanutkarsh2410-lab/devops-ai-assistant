"""Database optimizations: indexes, archived tables, and migration helpers."""
from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Boolean, JSON, Text,
    ForeignKey, Index, event, text
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .database import Base


# ── Archived Tables ─────────────────────────────────────────────────────

class ArchivedIncident(Base):
    """Archived incidents older than configured retention period."""
    __tablename__ = "archived_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False)
    service_name = Column(String, nullable=True)
    root_cause = Column(String, nullable=True)
    solution = Column(String, nullable=True)
    detected_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    auto_resolved = Column(Boolean, default=False)
    resolution_time_seconds = Column(Integer, nullable=True)
    extra_data = Column(JSON, nullable=True)
    archived_at = Column(DateTime, default=datetime.utcnow)


class ArchivedMetric(Base):
    """Archived metrics older than retention period (90 days)."""
    __tablename__ = "archived_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    archived_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_archived_metrics_service_time', 'service_name', 'timestamp'),
    )


# ── Additional Indexes (applied via __table_args__ on existing models) ──
# These are created via migration script below

OPTIMIZATION_INDEXES = [
    # Incidents
    "CREATE INDEX IF NOT EXISTS idx_incidents_user_status ON incidents(user_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_incidents_service_time ON incidents(service_name, detected_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_incidents_severity_time ON incidents(severity, detected_at DESC)",

    # Metrics
    "CREATE INDEX IF NOT EXISTS idx_metrics_service_metric_time ON metrics(service_name, metric_name, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_metrics_time_value ON metrics(timestamp DESC, value)",

    # Alerts
    "CREATE INDEX IF NOT EXISTS idx_alerts_user_resolved ON alerts(user_id, resolved, triggered_at DESC)",

    # Logs
    "CREATE INDEX IF NOT EXISTS idx_logs_service_level_time ON log_entries(service_name, level, timestamp DESC)",

    # Notification logs
    "CREATE INDEX IF NOT EXISTS idx_notif_logs_event_time ON notification_logs(event_type, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_notif_logs_status ON notification_logs(status, created_at DESC)",

    # Action logs
    "CREATE INDEX IF NOT EXISTS idx_action_logs_incident ON action_logs(incident_id, executed_at DESC)",

    # Predictive alerts
    "CREATE INDEX IF NOT EXISTS idx_pred_alerts_severity ON predictive_alerts(severity, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_pred_alerts_prevented ON predictive_alerts(prevented, created_at DESC)",
]

ROLLBACK_INDEXES = [
    "DROP INDEX IF EXISTS idx_incidents_user_status",
    "DROP INDEX IF EXISTS idx_incidents_service_time",
    "DROP INDEX IF EXISTS idx_incidents_severity_time",
    "DROP INDEX IF EXISTS idx_metrics_service_metric_time",
    "DROP INDEX IF EXISTS idx_metrics_time_value",
    "DROP INDEX IF EXISTS idx_alerts_user_resolved",
    "DROP INDEX IF EXISTS idx_logs_service_level_time",
    "DROP INDEX IF EXISTS idx_notif_logs_event_time",
    "DROP INDEX IF EXISTS idx_notif_logs_status",
    "DROP INDEX IF EXISTS idx_action_logs_incident",
    "DROP INDEX IF EXISTS idx_pred_alerts_severity",
    "DROP INDEX IF EXISTS idx_pred_alerts_prevented",
]


def apply_indexes(engine):
    """Apply all optimization indexes."""
    with engine.connect() as conn:
        for stmt in OPTIMIZATION_INDEXES:
            conn.execute(text(stmt))
        conn.commit()


def rollback_indexes(engine):
    """Remove all optimization indexes (rollback)."""
    with engine.connect() as conn:
        for stmt in ROLLBACK_INDEXES:
            conn.execute(text(stmt))
        conn.commit()
