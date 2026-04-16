"""
Capacity Planner: Predicts capacity needs, recommends scaling,
and helps plan for traffic events.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

import numpy as np

logger = logging.getLogger(__name__)


class CapacityPlanner:
    """Intelligent capacity planning based on metric forecasts."""

    # Default resource limits per service
    DEFAULT_LIMITS = {
        "cpu": 100.0,       # percent
        "memory": 100.0,    # percent
        "disk": 100.0,      # percent
        "connections": 500,  # max connections
    }

    # Cost per instance per hour (simplified)
    INSTANCE_COST_PER_HOUR = 0.10

    def __init__(self, api_get=None):
        self._api_get = api_get

    def calculate_current_capacity(self) -> Dict[str, Any]:
        """
        Calculate current resource capacity across services.

        Returns utilization, buffer remaining, and per-service breakdown.
        """
        services = self._get_services()
        capacity = {"services": {}, "overall": {}}

        total_util = []
        for svc in services:
            metrics = self._get_latest_metrics(svc)
            cpu = metrics.get("cpu", 0)
            memory = metrics.get("memory", 0)
            disk = metrics.get("disk", 0)

            utilization = max(cpu, memory, disk)
            buffer = 100 - utilization

            capacity["services"][svc] = {
                "cpu_percent": round(cpu, 1),
                "memory_percent": round(memory, 1),
                "disk_percent": round(disk, 1),
                "peak_utilization": round(utilization, 1),
                "buffer_percent": round(buffer, 1),
                "status": (
                    "critical" if buffer < 10 else
                    "warning" if buffer < 25 else
                    "healthy"
                ),
            }
            total_util.append(utilization)

        avg_util = np.mean(total_util) if total_util else 0
        capacity["overall"] = {
            "avg_utilization": round(float(avg_util), 1),
            "total_services": len(services),
            "critical_count": sum(
                1 for s in capacity["services"].values() if s["status"] == "critical"
            ),
            "healthy_count": sum(
                1 for s in capacity["services"].values() if s["status"] == "healthy"
            ),
        }

        return capacity

    def predict_capacity_breach(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Predict when capacity will be breached for each service.

        Returns per-service breach predictions with dates and recommendations.
        """
        from .prophet_forecaster import ProphetForecaster

        forecaster = ProphetForecaster(api_get=self._api_get)
        services = self._get_services()
        result = {"services": {}, "first_breach": None}

        for svc in services:
            svc_breach = {"will_breach": False, "metrics": {}}

            for metric in ["cpu", "memory"]:
                forecast = forecaster.forecast_metric(
                    svc, metric, horizon_hours=days_ahead * 24
                )
                if forecast.get("error"):
                    continue

                anomaly = forecaster.detect_anomalies_in_forecast(forecast)
                if anomaly.get("will_breach"):
                    hours = anomaly.get("hours_until_exhaustion")
                    days = hours / 24 if hours else None

                    svc_breach["will_breach"] = True
                    svc_breach["metric"] = metric
                    svc_breach["days_until_breach"] = round(days, 1) if days else None
                    svc_breach["breach_date"] = anomaly.get("first_breach_point", {}).get("ds")
                    svc_breach["confidence"] = 70 if forecast.get("method") == "prophet" else 55
                    svc_breach["recommendation"] = self._scaling_recommendation(
                        svc, metric, days
                    )
                    break  # first breaching metric is enough

            result["services"][svc] = svc_breach

            # Track earliest breach
            if svc_breach.get("days_until_breach"):
                if (
                    result["first_breach"] is None
                    or svc_breach["days_until_breach"] < result["first_breach"]["days"]
                ):
                    result["first_breach"] = {
                        "service": svc,
                        "days": svc_breach["days_until_breach"],
                        "metric": svc_breach.get("metric"),
                    }

        return result

    def recommend_scaling(self) -> List[Dict[str, Any]]:
        """
        Generate scaling recommendations based on current and predicted usage.
        """
        capacity = self.calculate_current_capacity()
        breach = self.predict_capacity_breach(days_ahead=14)
        recommendations = []

        for svc, info in capacity["services"].items():
            if info["status"] == "critical":
                recommendations.append({
                    "service": svc,
                    "action": "scale_up",
                    "urgency": "immediate",
                    "reason": f"Utilization at {info['peak_utilization']}%",
                    "recommendation": "Add 1-2 instances immediately",
                    "estimated_cost": f"${self.INSTANCE_COST_PER_HOUR * 720:.0f}/month",
                })
            elif info["status"] == "warning":
                breach_info = breach["services"].get(svc, {})
                days = breach_info.get("days_until_breach")
                if days and days < 14:
                    recommendations.append({
                        "service": svc,
                        "action": "scale_up",
                        "urgency": "planned",
                        "reason": f"Capacity breach predicted in {days:.0f} days",
                        "recommendation": f"Add 1 instance by {self._date_offset(days - 2)}",
                        "estimated_cost": f"${self.INSTANCE_COST_PER_HOUR * 720:.0f}/month",
                    })

        return sorted(recommendations, key=lambda x: 0 if x["urgency"] == "immediate" else 1)

    def optimize_resources(self) -> List[Dict[str, Any]]:
        """
        Identify over-provisioned services that could be scaled down.
        """
        capacity = self.calculate_current_capacity()
        optimizations = []

        for svc, info in capacity["services"].items():
            if info["peak_utilization"] < 20:
                savings = self.INSTANCE_COST_PER_HOUR * 720
                optimizations.append({
                    "service": svc,
                    "action": "scale_down",
                    "current_utilization": info["peak_utilization"],
                    "recommendation": f"Consider reducing instances for {svc}",
                    "potential_savings": f"${savings:.0f}/month",
                    "risk": "low",
                })

        return optimizations

    def plan_for_event(
        self,
        event_date: str,
        expected_traffic_multiplier: float,
        event_name: str = "Event",
    ) -> Dict[str, Any]:
        """
        Generate a scaling plan for a predicted traffic event.

        Args:
            event_date: ISO date string.
            expected_traffic_multiplier: e.g. 5.0 for "5x traffic".
            event_name: Name of the event.
        """
        capacity = self.calculate_current_capacity()
        plan = {
            "event_name": event_name,
            "event_date": event_date,
            "traffic_multiplier": expected_traffic_multiplier,
            "actions": [],
            "total_estimated_cost": 0,
        }

        for svc, info in capacity["services"].items():
            current_util = info["peak_utilization"]
            projected_util = current_util * expected_traffic_multiplier

            if projected_util > 80:
                # Need to scale
                scale_factor = projected_util / 70  # target 70% util after scaling
                additional_instances = max(1, int(np.ceil(scale_factor - 1)))
                cost = additional_instances * self.INSTANCE_COST_PER_HOUR * 24  # per day

                plan["actions"].append({
                    "service": svc,
                    "current_utilization": round(current_util, 1),
                    "projected_utilization": round(projected_util, 1),
                    "additional_instances": additional_instances,
                    "scale_up_date": self._date_offset_from(event_date, -1),
                    "scale_down_date": self._date_offset_from(event_date, 1),
                    "daily_cost": round(cost, 2),
                })
                plan["total_estimated_cost"] += cost

        plan["total_estimated_cost"] = round(plan["total_estimated_cost"], 2)
        plan["timeline"] = [
            {"date": self._date_offset_from(event_date, -2), "action": "Verify capacity plan"},
            {"date": self._date_offset_from(event_date, -1), "action": "Scale up services"},
            {"date": event_date, "action": f"{event_name} — monitor closely"},
            {"date": self._date_offset_from(event_date, 1), "action": "Scale down if traffic normalized"},
        ]

        return plan

    # ── Helpers ─────────────────────────────────────────────────────────

    def _get_services(self) -> List[str]:
        if not self._api_get:
            return ["api-server", "web-server", "worker-service", "database"]
        try:
            incidents = self._api_get("/incidents/", {"limit": 100})
            services = set()
            for inc in incidents:
                svc = inc.get("service_name")
                if svc:
                    services.add(svc)
            return list(services) or ["api-server", "web-server"]
        except Exception:
            return ["api-server", "web-server"]

    def _get_latest_metrics(self, service: str) -> dict:
        if not self._api_get:
            return {
                "cpu": float(np.random.uniform(30, 75)),
                "memory": float(np.random.uniform(40, 80)),
                "disk": float(np.random.uniform(20, 60)),
            }
        try:
            metrics = self._api_get("/metrics/", {
                "service_name": service, "hours": 1, "limit": 10
            })
            result = {}
            for m in metrics:
                result[m.get("metric_name", "")] = m.get("value", 0)
            return result
        except Exception:
            return {"cpu": 50, "memory": 60, "disk": 40}

    def _scaling_recommendation(
        self, service: str, metric: str, days_until_breach: float = None
    ) -> str:
        if days_until_breach and days_until_breach < 3:
            return f"URGENT: Scale up {service} immediately"
        elif days_until_breach and days_until_breach < 7:
            return f"Scale up {service} within {days_until_breach:.0f} days"
        else:
            return f"Plan to add capacity for {service} within 2 weeks"

    def _date_offset(self, days: float) -> str:
        return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")

    def _date_offset_from(self, base_date: str, offset_days: int) -> str:
        try:
            base = datetime.fromisoformat(base_date.replace("Z", ""))
            return (base + timedelta(days=offset_days)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return self._date_offset(offset_days)
