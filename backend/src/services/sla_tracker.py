"""SLA tracking service — uptime calculation, error budgets, breach detection."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.incident import Incident
from models.sla import SLAConfig, SLARecord


class SLATracker:
    """Tracks SLA compliance per service."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def get_configs(self) -> list[dict]:
        configs = (
            self.db.query(SLAConfig)
            .filter(SLAConfig.user_id == self.user_id)
            .all()
        )
        return [self._serialize_config(c) for c in configs]

    def create_config(self, service_name: str, target_uptime: float = 99.9,
                      max_mttr_minutes: int = 30, max_incidents: int | None = None) -> dict:
        # Error budget: minutes of allowed downtime per 30 days
        error_budget = (100 - target_uptime) / 100 * 30 * 24 * 60

        config = SLAConfig(
            user_id=self.user_id,
            service_name=service_name,
            target_uptime=target_uptime,
            max_mttr_minutes=max_mttr_minutes,
            max_incidents_per_month=max_incidents,
            error_budget_minutes=round(error_budget, 2),
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return self._serialize_config(config)

    def calculate_sla(self, service_name: str, days: int = 30) -> dict:
        """Calculate current SLA status for a service."""
        since = datetime.utcnow() - timedelta(days=days)
        total_minutes = days * 24 * 60

        # Get incidents for this service
        incidents = (
            self.db.query(Incident)
            .filter(
                Incident.user_id == self.user_id,
                Incident.service_name == service_name,
                Incident.detected_at >= since,
            )
            .all()
        )

        # Calculate downtime
        downtime_minutes = 0.0
        mttr_values = []
        breaches = []

        for inc in incidents:
            if inc.resolved_at and inc.detected_at:
                dt = (inc.resolved_at - inc.detected_at).total_seconds() / 60
                downtime_minutes += dt
                mttr_values.append(dt)
            elif inc.detected_at:
                # Unresolved — count from detection to now
                dt = (datetime.utcnow() - inc.detected_at).total_seconds() / 60
                downtime_minutes += dt

        uptime = max(0, (total_minutes - downtime_minutes) / total_minutes * 100)
        avg_mttr = sum(mttr_values) / len(mttr_values) if mttr_values else 0

        # Check against SLA config
        config = (
            self.db.query(SLAConfig)
            .filter(SLAConfig.user_id == self.user_id, SLAConfig.service_name == service_name)
            .first()
        )

        sla_met = True
        error_budget_remaining = 0.0

        if config:
            error_budget_remaining = max(0, config.error_budget_minutes - downtime_minutes)
            if uptime < config.target_uptime:
                sla_met = False
                breaches.append({
                    "type": "uptime",
                    "target": config.target_uptime,
                    "actual": round(uptime, 3),
                })
            if avg_mttr > config.max_mttr_minutes and mttr_values:
                breaches.append({
                    "type": "mttr",
                    "target": config.max_mttr_minutes,
                    "actual": round(avg_mttr, 1),
                })
            if config.max_incidents_per_month and len(incidents) > config.max_incidents_per_month:
                breaches.append({
                    "type": "incident_count",
                    "target": config.max_incidents_per_month,
                    "actual": len(incidents),
                })
                sla_met = False

        return {
            "service_name": service_name,
            "period_days": days,
            "uptime_percent": round(uptime, 4),
            "total_downtime_minutes": round(downtime_minutes, 1),
            "incidents_count": len(incidents),
            "avg_mttr_minutes": round(avg_mttr, 1),
            "error_budget_remaining_minutes": round(error_budget_remaining, 1),
            "error_budget_percent": round(
                error_budget_remaining / config.error_budget_minutes * 100, 1
            ) if config and config.error_budget_minutes > 0 else 100,
            "sla_met": sla_met,
            "breaches": breaches,
            "target_uptime": config.target_uptime if config else 99.9,
        }

    def calculate_all_slas(self, days: int = 30) -> list[dict]:
        """Calculate SLA for all configured services."""
        configs = (
            self.db.query(SLAConfig)
            .filter(SLAConfig.user_id == self.user_id)
            .all()
        )

        # Also include services with incidents but no config
        incident_services = (
            self.db.query(Incident.service_name)
            .filter(Incident.user_id == self.user_id, Incident.service_name.isnot(None))
            .distinct()
            .all()
        )

        all_services = set(c.service_name for c in configs)
        for (svc,) in incident_services:
            all_services.add(svc)

        return [self.calculate_sla(svc, days) for svc in sorted(all_services)]

    def _serialize_config(self, c: SLAConfig) -> dict:
        return {
            "id": str(c.id),
            "service_name": c.service_name,
            "target_uptime": c.target_uptime,
            "max_mttr_minutes": c.max_mttr_minutes,
            "max_incidents_per_month": c.max_incidents_per_month,
            "error_budget_minutes": c.error_budget_minutes,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
