"""Data archival and retention service.

Retention policy:
  - Metrics: 90 days → archive
  - Logs: 30 days → delete
  - Alerts: 180 days → delete
  - Incidents: keep all, archive resolved older than 365 days
  - Notification logs: 90 days → delete
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Retention periods (days)
RETENTION = {
    "metrics": 90,
    "logs": 30,
    "alerts": 180,
    "incidents": 365,
    "notification_logs": 90,
}


class ArchivalService:
    """Moves old data to archive tables and cleans up expired records."""

    def __init__(self, db: Session):
        self.db = db

    def run_full_cleanup(self) -> dict:
        """Run all archival and cleanup tasks. Returns summary."""
        results = {}
        results["metrics"] = self.archive_metrics()
        results["logs"] = self.cleanup_logs()
        results["alerts"] = self.cleanup_alerts()
        results["incidents"] = self.archive_incidents()
        results["notification_logs"] = self.cleanup_notification_logs()
        logger.info(f"Archival complete: {results}")
        return results

    def archive_metrics(self) -> int:
        """Move metrics older than 90 days to archived_metrics."""
        cutoff = datetime.utcnow() - timedelta(days=RETENTION["metrics"])
        try:
            # Copy to archive
            self.db.execute(text("""
                INSERT INTO archived_metrics (id, user_id, service_name, metric_name, value, unit, timestamp, archived_at)
                SELECT id, user_id, service_name, metric_name, value, unit, timestamp, NOW()
                FROM metrics
                WHERE timestamp < :cutoff
                ON CONFLICT (id) DO NOTHING
            """), {"cutoff": cutoff})

            # Delete originals
            result = self.db.execute(text(
                "DELETE FROM metrics WHERE timestamp < :cutoff"
            ), {"cutoff": cutoff})
            self.db.commit()
            count = result.rowcount
            logger.info(f"Archived {count} metrics older than {RETENTION['metrics']} days")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Metric archival failed: {e}")
            return 0

    def archive_incidents(self) -> int:
        """Archive resolved incidents older than 365 days."""
        cutoff = datetime.utcnow() - timedelta(days=RETENTION["incidents"])
        try:
            self.db.execute(text("""
                INSERT INTO archived_incidents
                    (id, user_id, title, description, severity, status, service_name,
                     root_cause, solution, detected_at, resolved_at, created_at,
                     auto_resolved, resolution_time_seconds, extra_data, archived_at)
                SELECT id, user_id, title, description, severity, status, service_name,
                       root_cause, solution, detected_at, resolved_at, created_at,
                       auto_resolved, resolution_time_seconds, metadata, NOW()
                FROM incidents
                WHERE status IN ('resolved', 'closed') AND created_at < :cutoff
                ON CONFLICT (id) DO NOTHING
            """), {"cutoff": cutoff})

            result = self.db.execute(text("""
                DELETE FROM incidents
                WHERE status IN ('resolved', 'closed') AND created_at < :cutoff
            """), {"cutoff": cutoff})
            self.db.commit()
            count = result.rowcount
            logger.info(f"Archived {count} incidents older than {RETENTION['incidents']} days")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Incident archival failed: {e}")
            return 0

    def cleanup_logs(self) -> int:
        """Delete log entries older than 30 days."""
        cutoff = datetime.utcnow() - timedelta(days=RETENTION["logs"])
        try:
            result = self.db.execute(text(
                "DELETE FROM log_entries WHERE timestamp < :cutoff"
            ), {"cutoff": cutoff})
            self.db.commit()
            count = result.rowcount
            logger.info(f"Deleted {count} log entries older than {RETENTION['logs']} days")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Log cleanup failed: {e}")
            return 0

    def cleanup_alerts(self) -> int:
        """Delete resolved alerts older than 180 days."""
        cutoff = datetime.utcnow() - timedelta(days=RETENTION["alerts"])
        try:
            result = self.db.execute(text(
                "DELETE FROM alerts WHERE resolved = true AND triggered_at < :cutoff"
            ), {"cutoff": cutoff})
            self.db.commit()
            count = result.rowcount
            logger.info(f"Deleted {count} alerts older than {RETENTION['alerts']} days")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Alert cleanup failed: {e}")
            return 0

    def cleanup_notification_logs(self) -> int:
        """Delete notification logs older than 90 days."""
        cutoff = datetime.utcnow() - timedelta(days=RETENTION["notification_logs"])
        try:
            result = self.db.execute(text(
                "DELETE FROM notification_logs WHERE created_at < :cutoff"
            ), {"cutoff": cutoff})
            self.db.commit()
            count = result.rowcount
            logger.info(f"Deleted {count} notification logs older than {RETENTION['notification_logs']} days")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Notification log cleanup failed: {e}")
            return 0

    def get_retention_stats(self) -> dict:
        """Get current data counts and retention info."""
        stats = {}
        tables = {
            "metrics": "metrics",
            "logs": "log_entries",
            "alerts": "alerts",
            "incidents": "incidents",
            "notification_logs": "notification_logs",
        }
        for key, table in tables.items():
            try:
                result = self.db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[key] = {
                    "count": count,
                    "retention_days": RETENTION[key],
                }
            except Exception:
                stats[key] = {"count": 0, "retention_days": RETENTION[key]}
        return stats
