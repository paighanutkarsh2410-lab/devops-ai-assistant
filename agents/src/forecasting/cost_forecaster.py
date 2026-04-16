"""
Cost Forecaster: Predicts infrastructure costs based on resource usage trends.
Identifies cost anomalies and recommends optimizations.
"""
import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

import numpy as np
import yaml

logger = logging.getLogger(__name__)

# Default pricing (per hour)
DEFAULT_PRICING = {
    "compute": 0.05,       # per instance-hour
    "storage": 0.0001,     # per GB-hour
    "network": 0.01,       # per GB transferred
    "database": 0.08,      # per connection-hour
}


class CostForecaster:
    """Predicts and optimizes infrastructure costs."""

    def __init__(self, api_get=None):
        self._api_get = api_get
        self._pricing = self._load_pricing()

    def calculate_current_costs(self) -> Dict[str, Any]:
        """
        Estimate current monthly infrastructure costs based on resource usage.
        """
        services = self._get_services()
        breakdown = {}
        total = 0.0

        for svc in services:
            metrics = self._get_latest_metrics(svc)
            cpu = metrics.get("cpu", 50)
            memory = metrics.get("memory", 50)

            # Compute cost (higher utilization = more cost)
            compute_hours = 730  # hours per month
            utilization_factor = max(cpu, memory) / 100
            instances = max(1, int(np.ceil(utilization_factor * 2)))
            compute_cost = instances * self._pricing["compute"] * compute_hours

            # Storage cost (estimate based on disk usage)
            disk_gb = metrics.get("disk", 30) * 1  # simplified
            storage_cost = disk_gb * self._pricing["storage"] * compute_hours

            # Network (estimated)
            network_cost = 5.0  # flat estimate per service

            service_total = compute_cost + storage_cost + network_cost

            breakdown[svc] = {
                "compute": round(compute_cost, 2),
                "storage": round(storage_cost, 2),
                "network": round(network_cost, 2),
                "total": round(service_total, 2),
                "instances": instances,
            }
            total += service_total

        return {
            "current_monthly": round(total, 2),
            "breakdown": breakdown,
            "pricing_model": self._pricing,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    def forecast_monthly_cost(self) -> Dict[str, Any]:
        """
        Predict next month's costs based on usage trends.
        """
        current = self.calculate_current_costs()
        current_total = current["current_monthly"]

        # Estimate growth from metric trends
        growth_factor = 1.0
        services = self._get_services()

        for svc in services[:3]:
            trend = self._estimate_growth_rate(svc)
            if trend > 0:
                growth_factor = max(growth_factor, 1 + trend)

        predicted_total = current_total * growth_factor

        # Per-service projected costs
        projected_breakdown = {}
        for svc, costs in current["breakdown"].items():
            projected_breakdown[svc] = {
                "current": costs["total"],
                "projected": round(costs["total"] * growth_factor, 2),
                "change_percent": round((growth_factor - 1) * 100, 1),
            }

        return {
            "current_monthly": round(current_total, 2),
            "predicted_total": round(predicted_total, 2),
            "change_percent": round((growth_factor - 1) * 100, 1),
            "growth_factor": round(growth_factor, 3),
            "projected_breakdown": projected_breakdown,
            "forecast_period": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def predict_cost_anomalies(self) -> List[Dict[str, Any]]:
        """Detect unusual cost spikes across services."""
        current = self.calculate_current_costs()
        anomalies = []

        # Compare each service to average
        totals = [c["total"] for c in current["breakdown"].values()]
        if not totals:
            return []

        avg_cost = np.mean(totals)
        std_cost = np.std(totals)

        for svc, costs in current["breakdown"].items():
            if std_cost > 0:
                z_score = (costs["total"] - avg_cost) / std_cost
                if z_score > 2.0:
                    anomalies.append({
                        "service": svc,
                        "cost": costs["total"],
                        "avg_cost": round(float(avg_cost), 2),
                        "z_score": round(float(z_score), 2),
                        "message": (
                            f"{svc} costs ${costs['total']:.0f}/month — "
                            f"{z_score:.1f}x standard deviations above average"
                        ),
                    })

        return anomalies

    def optimize_for_cost(self) -> List[Dict[str, Any]]:
        """Identify cost-saving opportunities."""
        current = self.calculate_current_costs()
        optimizations = []

        for svc, costs in current["breakdown"].items():
            metrics = self._get_latest_metrics(svc)
            cpu = metrics.get("cpu", 50)
            memory = metrics.get("memory", 50)
            peak = max(cpu, memory)

            # Over-provisioned services
            if peak < 30 and costs["instances"] > 1:
                savings = costs["compute"] * 0.5
                optimizations.append({
                    "service": svc,
                    "type": "right_size",
                    "description": f"Reduce instances for {svc} (utilization: {peak:.0f}%)",
                    "current_cost": costs["total"],
                    "potential_savings": round(savings, 2),
                    "risk": "low",
                    "recommendation": f"Scale down {svc} from {costs['instances']} to {max(1, costs['instances'] - 1)} instances",
                })

            # Reserved instance recommendations (if running 24/7)
            if costs["compute"] > 20:
                ri_savings = costs["compute"] * 0.3  # ~30% savings with reserved
                optimizations.append({
                    "service": svc,
                    "type": "reserved_instance",
                    "description": f"Switch {svc} to reserved instances",
                    "current_cost": costs["compute"],
                    "potential_savings": round(ri_savings, 2),
                    "risk": "medium",
                    "recommendation": f"Reserve instances for {svc} to save ~${ri_savings:.0f}/month",
                })

        total_savings = sum(o["potential_savings"] for o in optimizations)
        for opt in optimizations:
            opt["total_potential_savings"] = round(total_savings, 2)

        return sorted(optimizations, key=lambda x: x["potential_savings"], reverse=True)

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

    def _estimate_growth_rate(self, service: str) -> float:
        """Estimate monthly growth rate from recent metric trends."""
        if not self._api_get:
            return 0.05  # 5% default growth

        try:
            metrics = self._api_get("/metrics/", {
                "service_name": service,
                "metric_name": "cpu",
                "hours": 168,
                "limit": 500,
            })
            if len(metrics) < 20:
                return 0.03

            values = [float(m.get("value", 0)) for m in metrics]
            n = len(values)
            first_half = np.mean(values[:n // 2])
            second_half = np.mean(values[n // 2:])

            if first_half > 0:
                weekly_growth = (second_half - first_half) / first_half
                return max(0, weekly_growth * 4)  # extrapolate to monthly
            return 0.03
        except Exception:
            return 0.03

    def _load_pricing(self) -> dict:
        """Load pricing from config or use defaults."""
        pricing_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'pricing.yaml'
        )
        try:
            if os.path.exists(pricing_path):
                with open(pricing_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                    return config.get("pricing", DEFAULT_PRICING)
        except Exception:
            pass
        return DEFAULT_PRICING.copy()
