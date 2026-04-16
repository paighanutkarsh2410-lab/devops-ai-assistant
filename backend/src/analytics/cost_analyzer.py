"""Cost analytics engine — ROI calculation, optimization recommendations, allocation."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict
from models.incident import Incident
from models.action_log import ActionLog
from models.predictive_alert import PredictiveAlert


class CostAnalyzer:
    """Calculates ROI, cost allocation, and optimization recommendations."""

    DEFAULT_HOURLY_RATE = 75.0
    DEFAULT_DOWNTIME_COST_PER_HOUR = 500.0

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    # ── ROI Summary ────────────────────────────────────────────────────

    def roi_summary(self, days: int = 30, hourly_rate: float = None, downtime_cost: float = None) -> dict:
        rate = hourly_rate or self.DEFAULT_HOURLY_RATE
        dt_cost = downtime_cost or self.DEFAULT_DOWNTIME_COST_PER_HOUR
        since = datetime.utcnow() - timedelta(days=days)

        incidents = self._get_incidents(since)
        auto_resolved = [i for i in incidents if i.auto_resolved]
        manual_resolved = [i for i in incidents if not i.auto_resolved and i.resolved_at]

        # Time savings
        manual_avg_min = 30  # assumed avg manual resolution
        auto_times = [
            (i.resolution_time_seconds or 0) / 60 for i in auto_resolved
        ]
        time_saved_min = sum(max(0, manual_avg_min - t) for t in auto_times)
        hours_saved = time_saved_min / 60
        engineer_cost_saved = hours_saved * rate

        # Downtime prevention from predictions
        prevented = self.db.query(func.count(PredictiveAlert.id)).filter(
            PredictiveAlert.prevented == True
        ).scalar() or 0
        downtime_prevented_hours = prevented * 0.5
        downtime_cost_saved = downtime_prevented_hours * dt_cost

        # Total investment (rough estimate based on compute + platform costs)
        monthly_platform_cost = 200  # estimated hosting cost

        total_savings = engineer_cost_saved + downtime_cost_saved
        roi_percent = ((total_savings - monthly_platform_cost) / max(monthly_platform_cost, 1)) * 100

        return {
            "period_days": days,
            "incidents_total": len(incidents),
            "auto_resolved": len(auto_resolved),
            "manual_resolved": len(manual_resolved),
            "engineer_hours_saved": round(hours_saved, 1),
            "engineer_cost_saved": round(engineer_cost_saved, 2),
            "incidents_prevented": prevented,
            "downtime_prevented_hours": round(downtime_prevented_hours, 1),
            "downtime_cost_saved": round(downtime_cost_saved, 2),
            "total_savings": round(total_savings, 2),
            "platform_cost": monthly_platform_cost,
            "roi_percent": round(roi_percent, 1),
            "hourly_rate_used": rate,
            "downtime_rate_used": dt_cost,
        }

    # ── Cost by service ────────────────────────────────────────────────

    def cost_by_service(self, days: int = 30, hourly_rate: float = None) -> dict:
        rate = hourly_rate or self.DEFAULT_HOURLY_RATE
        since = datetime.utcnow() - timedelta(days=days)
        incidents = self._get_incidents(since)

        by_service: dict[str, dict] = defaultdict(lambda: {
            "incidents": 0, "downtime_min": 0, "auto_resolved": 0, "manual_resolved": 0,
        })

        for inc in incidents:
            svc = inc.service_name or "unknown"
            by_service[svc]["incidents"] += 1
            if inc.resolved_at and inc.detected_at:
                dt = (inc.resolved_at - inc.detected_at).total_seconds() / 60
                by_service[svc]["downtime_min"] += dt
            if inc.auto_resolved:
                by_service[svc]["auto_resolved"] += 1
            elif inc.resolved_at:
                by_service[svc]["manual_resolved"] += 1

        result = {}
        for svc, data in by_service.items():
            manual_cost = data["manual_resolved"] * 0.5 * rate  # 30 min avg
            downtime_cost = (data["downtime_min"] / 60) * self.DEFAULT_DOWNTIME_COST_PER_HOUR
            savings = data["auto_resolved"] * 0.5 * rate

            result[svc] = {
                **data,
                "downtime_hours": round(data["downtime_min"] / 60, 2),
                "manual_resolution_cost": round(manual_cost, 2),
                "downtime_cost": round(downtime_cost, 2),
                "total_cost": round(manual_cost + downtime_cost, 2),
                "automation_savings": round(savings, 2),
            }

        return {"period_days": days, "services": result}

    # ── Cost trend over time ───────────────────────────────────────────

    def cost_trend(self, days: int = 90, hourly_rate: float = None) -> dict:
        rate = hourly_rate or self.DEFAULT_HOURLY_RATE
        since = datetime.utcnow() - timedelta(days=days)
        incidents = self._get_incidents(since)

        weekly: dict[str, dict] = defaultdict(lambda: {"cost": 0, "savings": 0, "incidents": 0})

        for inc in incidents:
            if not inc.detected_at:
                continue
            week = inc.detected_at.strftime("%Y-W%W")
            weekly[week]["incidents"] += 1

            if inc.auto_resolved:
                weekly[week]["savings"] += 0.5 * rate
            elif inc.resolved_at:
                weekly[week]["cost"] += 0.5 * rate

            if inc.resolved_at and inc.detected_at:
                dt_hours = (inc.resolved_at - inc.detected_at).total_seconds() / 3600
                weekly[week]["cost"] += dt_hours * self.DEFAULT_DOWNTIME_COST_PER_HOUR

        weeks = []
        for wk in sorted(weekly.keys()):
            d = weekly[wk]
            weeks.append({
                "week": wk,
                "incident_cost": round(d["cost"], 2),
                "automation_savings": round(d["savings"], 2),
                "net_cost": round(d["cost"] - d["savings"], 2),
                "incidents": d["incidents"],
            })

        return {"period_days": days, "weekly_costs": weeks}

    # ── Optimization recommendations ───────────────────────────────────

    def optimization_recommendations(self, days: int = 30) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        incidents = self._get_incidents(since)

        recommendations = []

        # Find services with high manual resolution
        by_service: dict[str, dict] = defaultdict(lambda: {"total": 0, "auto": 0, "critical": 0})
        for inc in incidents:
            svc = inc.service_name or "unknown"
            by_service[svc]["total"] += 1
            if inc.auto_resolved:
                by_service[svc]["auto"] += 1
            if inc.severity == "critical":
                by_service[svc]["critical"] += 1

        for svc, data in by_service.items():
            auto_rate = data["auto"] / max(data["total"], 1)
            if auto_rate < 0.5 and data["total"] >= 3:
                potential_savings = (data["total"] - data["auto"]) * 0.5 * self.DEFAULT_HOURLY_RATE
                recommendations.append({
                    "type": "automation",
                    "service": svc,
                    "title": f"Increase automation for {svc}",
                    "description": f"Only {auto_rate*100:.0f}% auto-resolved. Improving could save ~${potential_savings:.0f}/month.",
                    "impact": "high" if potential_savings > 200 else "medium",
                    "potential_savings": round(potential_savings, 2),
                })

            if data["critical"] >= 3:
                recommendations.append({
                    "type": "prevention",
                    "service": svc,
                    "title": f"Reduce critical incidents for {svc}",
                    "description": f"{data['critical']} critical incidents. Consider proactive monitoring.",
                    "impact": "high",
                    "potential_savings": round(data["critical"] * self.DEFAULT_DOWNTIME_COST_PER_HOUR, 2),
                })

        # Check overall prediction usage
        pred_total = self.db.query(func.count(PredictiveAlert.id)).scalar() or 0
        pred_prevented = self.db.query(func.count(PredictiveAlert.id)).filter(
            PredictiveAlert.prevented == True
        ).scalar() or 0

        if pred_total > 0 and pred_prevented / pred_total < 0.3:
            recommendations.append({
                "type": "prediction",
                "service": "all",
                "title": "Act on more predictive alerts",
                "description": f"Only {pred_prevented}/{pred_total} predictions acted on. Prevention is cheaper than resolution.",
                "impact": "medium",
                "potential_savings": round((pred_total - pred_prevented) * 0.5 * self.DEFAULT_DOWNTIME_COST_PER_HOUR, 2),
            })

        # Sort by potential savings
        recommendations.sort(key=lambda r: r.get("potential_savings", 0), reverse=True)

        return {
            "period_days": days,
            "recommendations": recommendations,
            "total_potential_savings": round(sum(r.get("potential_savings", 0) for r in recommendations), 2),
        }

    # ── Helpers ─────────────────────────────────────────────────────────

    def _get_incidents(self, since: datetime) -> list:
        return (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.detected_at >= since)
            .all()
        )
