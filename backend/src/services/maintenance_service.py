"""Maintenance window service — scheduling, alert suppression, completion reports."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.maintenance_window import MaintenanceWindow
import logging

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Manages maintenance windows with alert suppression and notifications."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def schedule_maintenance(self, title: str, description: str, start_time: datetime,
                             end_time: datetime, affected_services: list, planned_actions: list) -> dict:
        """Create a new maintenance window."""
        # Validate time
        if start_time >= end_time:
            return {"error": "End time must be after start time"}
        if start_time < datetime.utcnow() - timedelta(minutes=5):
            return {"error": "Start time cannot be in the past"}

        # Check for conflicts
        conflicts = self._check_conflicts(start_time, end_time, affected_services)
        if conflicts:
            return {"error": "Conflicting maintenance window exists", "conflicts": conflicts}

        window = MaintenanceWindow(
            user_id=self.user_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            affected_services=affected_services,
            planned_actions=planned_actions,
            status="scheduled",
        )
        self.db.add(window)
        self.db.commit()
        self.db.refresh(window)

        return self._serialize(window)

    def start_maintenance(self, window_id: str) -> dict:
        """Mark a maintenance window as in-progress."""
        window = self._get_owned(window_id)
        if not window:
            return {"error": "Maintenance window not found"}
        if window.status != "scheduled":
            return {"error": f"Cannot start window in '{window.status}' status"}

        window.status = "in_progress"
        window.actual_start = datetime.utcnow()
        self.db.commit()

        return self._serialize(window)

    def end_maintenance(self, window_id: str, notes: str = None) -> dict:
        """Complete a maintenance window and generate report."""
        window = self._get_owned(window_id)
        if not window:
            return {"error": "Maintenance window not found"}
        if window.status != "in_progress":
            return {"error": f"Cannot end window in '{window.status}' status"}

        now = datetime.utcnow()
        window.status = "completed"
        window.actual_end = now

        # Generate completion report
        planned_duration = (window.end_time - window.start_time).total_seconds() / 60
        actual_duration = (now - window.actual_start).total_seconds() / 60 if window.actual_start else 0

        window.completion_report = {
            "planned_duration_minutes": round(planned_duration, 1),
            "actual_duration_minutes": round(actual_duration, 1),
            "on_time": actual_duration <= planned_duration * 1.1,  # 10% grace
            "services_affected": window.affected_services,
            "actions_completed": window.planned_actions,
            "notes": notes,
            "completed_at": now.isoformat(),
        }

        self.db.commit()
        return self._serialize(window)

    def cancel_maintenance(self, window_id: str) -> dict:
        """Cancel a scheduled maintenance window."""
        window = self._get_owned(window_id)
        if not window:
            return {"error": "Maintenance window not found"}
        if window.status not in ("scheduled",):
            return {"error": f"Cannot cancel window in '{window.status}' status"}

        window.status = "cancelled"
        self.db.commit()
        return self._serialize(window)

    def get_upcoming(self, days: int = 30) -> list[dict]:
        """Get upcoming maintenance windows."""
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        windows = (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.user_id == self.user_id,
                MaintenanceWindow.start_time >= now,
                MaintenanceWindow.start_time <= future,
                MaintenanceWindow.status.in_(["scheduled", "in_progress"]),
            )
            .order_by(MaintenanceWindow.start_time.asc())
            .all()
        )
        return [self._serialize(w) for w in windows]

    def get_all(self, status: str = None, limit: int = 50) -> list[dict]:
        """Get all maintenance windows."""
        q = self.db.query(MaintenanceWindow).filter(MaintenanceWindow.user_id == self.user_id)
        if status:
            q = q.filter(MaintenanceWindow.status == status)
        windows = q.order_by(MaintenanceWindow.start_time.desc()).limit(limit).all()
        return [self._serialize(w) for w in windows]

    def is_in_maintenance(self, service_name: str) -> dict:
        """Check if a service is currently in a maintenance window."""
        now = datetime.utcnow()
        active = (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.user_id == self.user_id,
                MaintenanceWindow.status == "in_progress",
            )
            .all()
        )

        for window in active:
            services = window.affected_services or []
            if service_name in services or not services:
                return {
                    "in_maintenance": True,
                    "window_id": str(window.id),
                    "title": window.title,
                    "ends_at": window.end_time.isoformat() if window.end_time else None,
                    "suppress_alerts": True,
                }

        return {"in_maintenance": False, "suppress_alerts": False}

    def get_needs_reminder(self) -> list[dict]:
        """Get windows that need reminder notifications."""
        now = datetime.utcnow()
        soon = now + timedelta(hours=1)

        windows = (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.user_id == self.user_id,
                MaintenanceWindow.status == "scheduled",
                MaintenanceWindow.start_time <= soon,
                MaintenanceWindow.start_time > now,
                MaintenanceWindow.reminder_sent == False,
            )
            .all()
        )
        return [self._serialize(w) for w in windows]

    def _check_conflicts(self, start: datetime, end: datetime, services: list) -> list[dict]:
        existing = (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.user_id == self.user_id,
                MaintenanceWindow.status.in_(["scheduled", "in_progress"]),
                MaintenanceWindow.start_time < end,
                MaintenanceWindow.end_time > start,
            )
            .all()
        )

        conflicts = []
        for w in existing:
            overlapping_services = set(w.affected_services or []) & set(services)
            if overlapping_services or not services or not w.affected_services:
                conflicts.append({
                    "id": str(w.id),
                    "title": w.title,
                    "start_time": w.start_time.isoformat(),
                    "end_time": w.end_time.isoformat(),
                    "overlapping_services": list(overlapping_services),
                })
        return conflicts

    def _get_owned(self, window_id: str) -> MaintenanceWindow | None:
        return self.db.query(MaintenanceWindow).filter(
            MaintenanceWindow.id == window_id, MaintenanceWindow.user_id == self.user_id
        ).first()

    def _serialize(self, w: MaintenanceWindow) -> dict:
        return {
            "id": str(w.id),
            "title": w.title,
            "description": w.description,
            "start_time": w.start_time.isoformat() if w.start_time else None,
            "end_time": w.end_time.isoformat() if w.end_time else None,
            "affected_services": w.affected_services,
            "planned_actions": w.planned_actions,
            "status": w.status,
            "actual_start": w.actual_start.isoformat() if w.actual_start else None,
            "actual_end": w.actual_end.isoformat() if w.actual_end else None,
            "completion_report": w.completion_report,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
