"""
Capacity Planning Agent: Tracks resource usage trends over days/weeks,
predicts when resources will be exhausted, and recommends scaling decisions.
Extends the Prediction Agent with longer time horizons and capacity-focused analysis.
"""
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from base_agent import BaseAgent
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

# Resource thresholds
THRESHOLDS = {
    "cpu_percent": {"warning": 70, "critical": 85, "unit": "%"},
    "memory_percent": {"warning": 75, "critical": 90, "unit": "%"},
    "disk_percent": {"warning": 80, "critical": 90, "unit": "%"},
    "network_bandwidth_percent": {"warning": 70, "critical": 85, "unit": "%"},
    "connection_pool_percent": {"warning": 75, "critical": 90, "unit": "%"},
    "iops_percent": {"warning": 70, "critical": 85, "unit": "%"},
}

SERVICES = ["api-server", "auth-service", "db-primary", "cache-redis", "worker-queue", "web-frontend"]


class CapacityPlanningAgent(BaseAgent):
    """Analyzes resource trends and predicts capacity exhaustion."""

    def __init__(self):
        super().__init__("CapacityPlanningAgent")
        self._history: Dict[str, List[Dict]] = {}  # service:metric → data points
        self._predictions: List[Dict] = []
        self._last_report = datetime.now(timezone.utc)
        self._report_interval = 3600  # Full report every hour
        self._tick_count = 0

    def tick(self):
        """Collect resource metrics, analyze trends, and generate predictions."""
        self._tick_count += 1

        # Collect current metrics for all services
        for service in SERVICES:
            self._collect_metrics(service)

        # Analyze trends and predict exhaustion
        predictions = self._analyze_all_trends()
        if predictions:
            self._predictions = predictions
            self._report_predictions(predictions)

        # Generate full capacity report periodically
        now = datetime.now(timezone.utc)
        if (now - self._last_report).total_seconds() >= self._report_interval:
            self._last_report = now
            self._generate_capacity_report()

    def _collect_metrics(self, service: str):
        """Collect current resource usage for a service."""
        try:
            metrics = self.api_get(f"/metrics/latest", {"service": service})
            if not metrics:
                return

            timestamp = datetime.now(timezone.utc).isoformat()

            # Store data points for trend analysis
            for metric_name in ["cpu_percent", "memory_percent", "disk_percent"]:
                value = None
                if isinstance(metrics, dict):
                    value = metrics.get(metric_name)
                elif isinstance(metrics, list):
                    for m in metrics:
                        if m.get("metric_name") == metric_name:
                            value = m.get("value")
                            break

                if value is not None:
                    key = f"{service}:{metric_name}"
                    if key not in self._history:
                        self._history[key] = []
                    self._history[key].append({
                        "timestamp": timestamp,
                        "value": float(value),
                    })
                    # Keep last 168 data points (7 days at hourly collection)
                    self._history[key] = self._history[key][-168:]

        except Exception as e:
            logger.debug(f"Failed to collect metrics for {service}: {e}")

    def _analyze_all_trends(self) -> List[Dict]:
        """Analyze all stored metrics for exhaustion trends."""
        predictions = []

        for key, data_points in self._history.items():
            if len(data_points) < 5:  # Need at least 5 data points
                continue

            service, metric = key.split(":", 1)
            threshold_config = THRESHOLDS.get(metric, {"warning": 75, "critical": 90, "unit": "%"})

            # Calculate trend
            trend = self._calculate_trend(data_points)
            if trend is None:
                continue

            current_value = data_points[-1]["value"]
            growth_rate = trend["slope_per_hour"]

            # Skip if no growth or declining
            if growth_rate <= 0.01:
                continue

            # Predict when warning/critical thresholds will be hit
            warning_threshold = threshold_config["warning"]
            critical_threshold = threshold_config["critical"]

            hours_to_warning = None
            hours_to_critical = None

            if current_value < warning_threshold:
                hours_to_warning = (warning_threshold - current_value) / growth_rate
            if current_value < critical_threshold:
                hours_to_critical = (critical_threshold - current_value) / growth_rate

            # Only report if exhaustion is within 7 days (168 hours)
            if hours_to_critical and hours_to_critical <= 168:
                urgency = "critical" if hours_to_critical <= 24 else "high" if hours_to_critical <= 72 else "medium"

                predictions.append({
                    "service": service,
                    "metric": metric,
                    "current_value": round(current_value, 1),
                    "growth_rate_per_hour": round(growth_rate, 3),
                    "growth_rate_per_day": round(growth_rate * 24, 1),
                    "hours_to_warning": round(hours_to_warning, 1) if hours_to_warning else None,
                    "hours_to_critical": round(hours_to_critical, 1) if hours_to_critical else None,
                    "predicted_exhaustion": (datetime.now(timezone.utc) + timedelta(hours=hours_to_critical)).isoformat(),
                    "urgency": urgency,
                    "trend": trend,
                    "unit": threshold_config["unit"],
                    "recommendation": self._get_recommendation(service, metric, current_value, hours_to_critical, growth_rate),
                })

        return sorted(predictions, key=lambda p: p.get("hours_to_critical", 999))

    def _calculate_trend(self, data_points: List[Dict]) -> Optional[Dict]:
        """Calculate linear trend using least squares regression."""
        n = len(data_points)
        if n < 3:
            return None

        # Convert timestamps to hours from first point
        try:
            t0 = datetime.fromisoformat(data_points[0]["timestamp"].replace("Z", "+00:00"))
            x = []
            y = []
            for dp in data_points:
                t = datetime.fromisoformat(dp["timestamp"].replace("Z", "+00:00"))
                hours = (t - t0).total_seconds() / 3600
                x.append(hours)
                y.append(dp["value"])
        except (ValueError, KeyError):
            return None

        # Linear regression: y = mx + b
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-10:
            return None

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        # R-squared (coefficient of determination)
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Volatility (standard deviation of residuals)
        residuals = [yi - (slope * xi + intercept) for xi, yi in zip(x, y)]
        volatility = math.sqrt(sum(r ** 2 for r in residuals) / n) if n > 0 else 0

        return {
            "slope_per_hour": slope,
            "intercept": intercept,
            "r_squared": round(r_squared, 4),
            "volatility": round(volatility, 2),
            "data_points": n,
            "time_span_hours": round(x[-1] - x[0], 1) if x else 0,
            "direction": "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable",
        }

    def _get_recommendation(self, service: str, metric: str, current: float, hours_to_critical: float, growth_rate: float) -> str:
        """Generate actionable recommendation based on prediction."""
        days = hours_to_critical / 24

        metric_recs = {
            "cpu_percent": {
                "short": f"CPU on {service} will reach critical in {days:.0f} days. Scale horizontally by adding replicas or optimize hot code paths.",
                "action": "scale_horizontal" if days < 3 else "optimize_code",
            },
            "memory_percent": {
                "short": f"Memory on {service} will exhaust in {days:.0f} days. Check for memory leaks, increase memory limits, or restart to reclaim.",
                "action": "increase_memory" if days < 3 else "investigate_leaks",
            },
            "disk_percent": {
                "short": f"Disk on {service} will fill in {days:.0f} days. Set up log rotation, clean old data, or expand volume.",
                "action": "expand_disk" if days < 2 else "cleanup_logs",
            },
        }

        rec = metric_recs.get(metric, {})
        return rec.get("short", f"{metric} on {service} trending toward critical in {days:.0f} days. Investigate and plan capacity increase.")

    def _report_predictions(self, predictions: List[Dict]):
        """Report capacity predictions to the backend."""
        for pred in predictions:
            if pred["urgency"] in ("critical", "high"):
                try:
                    self.api_post("/alerts/predictive", {
                        "title": f"Capacity: {pred['metric'].replace('_', ' ')} on {pred['service']}",
                        "prediction_type": "capacity_exhaustion",
                        "service_name": pred["service"],
                        "confidence": int(pred["trend"]["r_squared"] * 100),
                        "hours_until_issue": pred["hours_to_critical"],
                        "current_value": pred["current_value"],
                        "predicted_value": THRESHOLDS.get(pred["metric"], {}).get("critical", 90),
                        "preventive_actions": [
                            {"action": "investigate", "description": pred["recommendation"]},
                        ],
                    })
                    print(f"  [CapacityAgent] Predicted {pred['metric']} exhaustion on {pred['service']} in {pred['hours_to_critical']:.0f}h")
                except Exception as e:
                    logger.warning(f"Failed to report prediction: {e}")

    def _generate_capacity_report(self):
        """Generate a comprehensive capacity report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services_monitored": len(set(k.split(":")[0] for k in self._history)),
            "metrics_tracked": len(self._history),
            "total_data_points": sum(len(v) for v in self._history.values()),
            "predictions": self._predictions,
            "resource_summary": {},
        }

        # Summary per service
        for key, data_points in self._history.items():
            if not data_points:
                continue
            service, metric = key.split(":", 1)
            if service not in report["resource_summary"]:
                report["resource_summary"][service] = {}

            current = data_points[-1]["value"]
            trend = self._calculate_trend(data_points)

            report["resource_summary"][service][metric] = {
                "current": round(current, 1),
                "trend": trend["direction"] if trend else "unknown",
                "growth_per_day": round(trend["slope_per_hour"] * 24, 2) if trend else 0,
            }

        try:
            self.api_post("/capacity/report", report)
        except Exception:
            pass  # Backend endpoint may not exist yet

        return report

    def get_capacity_overview(self) -> Dict[str, Any]:
        """Return current capacity overview for API consumption."""
        overview = {
            "services": {},
            "predictions": self._predictions[:10],
            "total_metrics_tracked": len(self._history),
        }

        for key, data_points in self._history.items():
            if not data_points:
                continue
            service, metric = key.split(":", 1)
            if service not in overview["services"]:
                overview["services"][service] = {"metrics": {}, "health": "healthy"}

            current = data_points[-1]["value"]
            trend = self._calculate_trend(data_points)
            threshold = THRESHOLDS.get(metric, {})

            status = "healthy"
            if current >= threshold.get("critical", 90):
                status = "critical"
            elif current >= threshold.get("warning", 75):
                status = "warning"

            overview["services"][service]["metrics"][metric] = {
                "current": round(current, 1),
                "status": status,
                "trend": trend["direction"] if trend else "stable",
                "growth_rate_daily": round(trend["slope_per_hour"] * 24, 2) if trend else 0,
            }

            # Service overall health is the worst metric status
            if status == "critical":
                overview["services"][service]["health"] = "critical"
            elif status == "warning" and overview["services"][service]["health"] != "critical":
                overview["services"][service]["health"] = "warning"

        return overview

    def get_stats(self) -> Dict[str, Any]:
        """Return agent statistics."""
        return {
            "tick_count": self._tick_count,
            "services_tracked": len(set(k.split(":")[0] for k in self._history)),
            "metrics_tracked": len(self._history),
            "total_data_points": sum(len(v) for v in self._history.values()),
            "active_predictions": len(self._predictions),
            "last_report": self._last_report.isoformat(),
        }
