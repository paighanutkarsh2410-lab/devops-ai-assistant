"""Comprehensive analytics engine for incident and system data.

Provides: MTTR, MTTD, MTBF, incident frequency, root cause distribution,
service reliability scores, blast radius, effectiveness metrics, cost impact.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from collections import Counter
from models.incident import Incident
from models.action_log import ActionLog
from models.alert import Alert
from models.predictive_alert import PredictiveAlert


class AnalyticsEngine:
    """Core analytics engine for DevOps metrics."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    # ── MTTR ────────────────────────────────────────────────

    def calculate_mttr(
        self, date_from: datetime = None, date_to: datetime = None, filters: dict = None
    ) -> dict:
        """Mean Time To Resolve — avg time from detection to resolution."""
        q = self._incident_query(date_from, date_to)
        q = q.filter(Incident.resolved_at.isnot(None))

        if filters:
            if filters.get("severity"):
                q = q.filter(Incident.severity == filters["severity"])
            if filters.get("service_name"):
                q = q.filter(Incident.service_name == filters["service_name"])

        incidents = q.all()
        if not incidents:
            return {"mttr_seconds": 0, "mttr_minutes": 0, "count": 0, "by_severity": {}, "by_service": {}}

        times = []
        by_severity: dict[str, list[float]] = {}
        by_service: dict[str, list[float]] = {}

        for inc in incidents:
            delta = (inc.resolved_at - inc.detected_at).total_seconds()
            times.append(delta)
            by_severity.setdefault(inc.severity, []).append(delta)
            if inc.service_name:
                by_service.setdefault(inc.service_name, []).append(delta)

        avg = sum(times) / len(times)
        return {
            "mttr_seconds": round(avg),
            "mttr_minutes": round(avg / 60, 1),
            "count": len(times),
            "by_severity": {k: round(sum(v) / len(v) / 60, 1) for k, v in by_severity.items()},
            "by_service": {k: round(sum(v) / len(v) / 60, 1) for k, v in by_service.items()},
        }

    # ── MTTD ────────────────────────────────────────────────

    def calculate_mttd(self, date_from: datetime = None, date_to: datetime = None) -> dict:
        """Mean Time To Detect — measures monitoring effectiveness."""
        q = self._incident_query(date_from, date_to)
        incidents = q.all()

        if not incidents:
            return {"mttd_seconds": 0, "count": 0}

        # MTTD approximated as time from created_at to detected_at
        # In practice, detected_at ≈ created_at for auto-detected incidents
        times = []
        for inc in incidents:
            if inc.created_at and inc.detected_at:
                delta = abs((inc.detected_at - inc.created_at).total_seconds())
                times.append(delta)

        avg = sum(times) / len(times) if times else 0
        return {
            "mttd_seconds": round(avg),
            "mttd_minutes": round(avg / 60, 1),
            "count": len(times),
        }

    # ── MTBF ────────────────────────────────────────────────

    def calculate_mtbf(self, service_name: str) -> dict:
        """Mean Time Between Failures for a specific service."""
        incidents = (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.service_name == service_name)
            .order_by(Incident.detected_at.asc())
            .all()
        )

        if len(incidents) < 2:
            return {"mtbf_hours": None, "incident_count": len(incidents), "service": service_name}

        gaps = []
        for i in range(1, len(incidents)):
            gap = (incidents[i].detected_at - incidents[i - 1].detected_at).total_seconds()
            gaps.append(gap)

        avg_gap = sum(gaps) / len(gaps)
        return {
            "mtbf_hours": round(avg_gap / 3600, 1),
            "mtbf_days": round(avg_gap / 86400, 1),
            "incident_count": len(incidents),
            "service": service_name,
        }

    # ── Incident frequency ──────────────────────────────────

    def incident_frequency_analysis(self, days: int = 30) -> dict:
        """Incidents per day/week with trend detection."""
        since = datetime.utcnow() - timedelta(days=days)
        incidents = self._incident_query(date_from=since).all()

        daily: dict[str, int] = {}
        for inc in incidents:
            day = inc.detected_at.strftime("%Y-%m-%d") if inc.detected_at else "unknown"
            daily[day] = daily.get(day, 0) + 1

        # Trend: compare first half vs second half
        sorted_days = sorted(daily.items())
        mid = len(sorted_days) // 2
        first_half = sum(v for _, v in sorted_days[:mid]) if mid else 0
        second_half = sum(v for _, v in sorted_days[mid:]) if mid else 0

        if first_half > 0:
            trend_pct = round((second_half - first_half) / first_half * 100, 1)
        else:
            trend_pct = 0

        return {
            "total": len(incidents),
            "daily": daily,
            "avg_per_day": round(len(incidents) / max(days, 1), 1),
            "trend": "increasing" if trend_pct > 10 else "decreasing" if trend_pct < -10 else "stable",
            "trend_pct": trend_pct,
        }

    # ── Root cause distribution ─────────────────────────────

    def root_cause_distribution(self) -> dict:
        """Most common root causes as chart data."""
        incidents = (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.root_cause.isnot(None))
            .all()
        )

        causes = Counter()
        for inc in incidents:
            # Normalize root cause to category
            rc = (inc.root_cause or "").lower()
            if "memory" in rc:
                causes["Memory Issues"] += 1
            elif "cpu" in rc:
                causes["CPU Overload"] += 1
            elif "timeout" in rc or "latency" in rc:
                causes["Timeout/Latency"] += 1
            elif "disk" in rc or "storage" in rc:
                causes["Disk/Storage"] += 1
            elif "deploy" in rc:
                causes["Deployment Issues"] += 1
            elif "network" in rc or "connection" in rc:
                causes["Network Issues"] += 1
            elif "database" in rc or "query" in rc:
                causes["Database Issues"] += 1
            else:
                causes["Other"] += 1

        total = sum(causes.values()) or 1
        return {
            "distribution": [
                {"cause": k, "count": v, "percentage": round(v / total * 100, 1)}
                for k, v in causes.most_common()
            ],
            "total_analyzed": total,
        }

    # ── Service reliability score ───────────────────────────

    def service_reliability_score(self, service_name: str = None) -> dict:
        """0-100 reliability score per service."""
        services = {}
        q = self.db.query(Incident).filter(Incident.user_id == self.user_id)
        if service_name:
            q = q.filter(Incident.service_name == service_name)

        incidents = q.all()

        # Group by service
        by_service: dict[str, list] = {}
        for inc in incidents:
            svc = inc.service_name or "unknown"
            by_service.setdefault(svc, []).append(inc)

        for svc, incs in by_service.items():
            total = len(incs)
            resolved = sum(1 for i in incs if i.status in ("resolved", "closed"))
            auto_resolved = sum(1 for i in incs if i.auto_resolved)
            critical = sum(1 for i in incs if i.severity == "critical")

            # Score components (higher is better)
            resolution_rate = (resolved / max(total, 1)) * 30  # max 30 points
            auto_rate = (auto_resolved / max(total, 1)) * 25  # max 25 points
            low_critical = max(0, 25 - critical * 5)  # max 25 points, -5 per critical
            low_frequency = max(0, 20 - total * 2)  # max 20 points, -2 per incident

            score = min(100, round(resolution_rate + auto_rate + low_critical + low_frequency))
            services[svc] = {
                "score": score,
                "incidents": total,
                "resolved": resolved,
                "auto_resolved": auto_resolved,
                "critical_count": critical,
                "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
            }

        return services

    # ── Blast radius ────────────────────────────────────────

    def calculate_blast_radius(self, incident_id: str) -> dict:
        """Estimate impact of a specific incident."""
        incident = (
            self.db.query(Incident)
            .filter(Incident.id == incident_id, Incident.user_id == self.user_id)
            .first()
        )
        if not incident:
            return {"error": "Incident not found"}

        # Find related incidents (same time window, different services)
        window_start = incident.detected_at - timedelta(minutes=15)
        window_end = (incident.resolved_at or incident.detected_at) + timedelta(minutes=15)

        related = (
            self.db.query(Incident)
            .filter(
                Incident.user_id == self.user_id,
                Incident.id != incident_id,
                Incident.detected_at.between(window_start, window_end),
            )
            .all()
        )

        affected_services = set()
        affected_services.add(incident.service_name or "unknown")
        for r in related:
            if r.service_name:
                affected_services.add(r.service_name)

        downtime_seconds = 0
        if incident.resolved_at:
            downtime_seconds = int((incident.resolved_at - incident.detected_at).total_seconds())

        severity_multiplier = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        impact_score = severity_multiplier.get(incident.severity, 1) * len(affected_services)

        return {
            "incident_id": str(incident_id),
            "services_affected": list(affected_services),
            "related_incidents": len(related),
            "downtime_seconds": downtime_seconds,
            "impact_score": impact_score,
            "severity": incident.severity,
        }

    # ── Effectiveness metrics ───────────────────────────────

    def effectiveness_metrics(self) -> dict:
        """How effective is the automation?"""
        incidents = self._incident_query().all()
        total = len(incidents) or 1
        resolved = sum(1 for i in incidents if i.status in ("resolved", "closed"))
        auto_resolved = sum(1 for i in incidents if i.auto_resolved)

        # Prediction accuracy
        pred_total = self.db.query(func.count(PredictiveAlert.id)).scalar() or 0
        pred_prevented = self.db.query(func.count(PredictiveAlert.id)).filter(
            PredictiveAlert.prevented == True
        ).scalar() or 0

        # Action success rate
        actions_total = self.db.query(func.count(ActionLog.id)).scalar() or 0
        actions_success = self.db.query(func.count(ActionLog.id)).filter(
            ActionLog.status == "completed"
        ).scalar() or 0

        return {
            "auto_remediation_rate": round(auto_resolved / total * 100, 1),
            "resolution_rate": round(resolved / total * 100, 1),
            "prediction_prevention_rate": round(pred_prevented / max(pred_total, 1) * 100, 1),
            "action_success_rate": round(actions_success / max(actions_total, 1) * 100, 1),
            "total_incidents": total,
            "auto_resolved": auto_resolved,
            "predictions_total": pred_total,
            "predictions_prevented": pred_prevented,
        }

    # ── Cost impact ─────────────────────────────────────────

    def cost_impact_analysis(self, hourly_engineer_cost: float = 75.0) -> dict:
        """Calculate cost savings from automation."""
        incidents = self._incident_query().all()
        auto_resolved = [i for i in incidents if i.auto_resolved and i.resolution_time_seconds]

        # Time saved: assume manual resolution takes 30 min avg
        manual_avg_minutes = 30
        auto_time_saved_minutes = sum(
            max(0, manual_avg_minutes - (i.resolution_time_seconds or 0) / 60)
            for i in auto_resolved
        )

        hours_saved = round(auto_time_saved_minutes / 60, 1)
        cost_saved = round(hours_saved * hourly_engineer_cost, 2)

        # Downtime prevented
        predicted = self.db.query(func.count(PredictiveAlert.id)).filter(
            PredictiveAlert.prevented == True
        ).scalar() or 0
        downtime_prevented_hours = predicted * 0.5  # Assume 30 min avg per prevented incident

        return {
            "incidents_auto_resolved": len(auto_resolved),
            "engineer_hours_saved": hours_saved,
            "cost_saved_usd": cost_saved,
            "downtime_prevented_hours": round(downtime_prevented_hours, 1),
            "downtime_cost_saved_usd": round(downtime_prevented_hours * hourly_engineer_cost * 5, 2),  # 5x multiplier for downtime
            "total_savings_usd": round(cost_saved + downtime_prevented_hours * hourly_engineer_cost * 5, 2),
            "hourly_rate_used": hourly_engineer_cost,
        }

    # ── Helpers ─────────────────────────────────────────────

    def _incident_query(self, date_from: datetime = None, date_to: datetime = None):
        q = self.db.query(Incident).filter(Incident.user_id == self.user_id)
        if date_from:
            q = q.filter(Incident.detected_at >= date_from)
        if date_to:
            q = q.filter(Incident.detected_at <= date_to)
        return q
