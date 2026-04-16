"""
Prediction Agent: Forecasts infrastructure problems before they happen.
Uses Prophet/linear regression, capacity planning, and trend detection
to generate predictive alerts and scaling recommendations.
"""
import sys
import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from base_agent import BaseAgent
from config import BACKEND_URL
from forecasting.prophet_forecaster import ProphetForecaster
from forecasting.capacity_planner import CapacityPlanner
from forecasting.trend_detector import TrendDetector
from forecasting.cost_forecaster import CostForecaster

logger = logging.getLogger(__name__)


class PredictionAgent(BaseAgent):
    """Agent that predicts infrastructure issues before they occur."""

    def __init__(self):
        super().__init__("PredictionAgent")
        self._tick_count = 0
        self._forecaster = None
        self._capacity_planner = None
        self._trend_detector = None
        self._cost_forecaster = None

    def _init_components(self):
        """Lazy-init components after authentication (need api_get)."""
        if self._forecaster is None:
            self._forecaster = ProphetForecaster(api_get=self.api_get)
            self._capacity_planner = CapacityPlanner(api_get=self.api_get)
            self._trend_detector = TrendDetector(api_get=self.api_get)
            self._cost_forecaster = CostForecaster(api_get=self.api_get)

    def tick(self):
        """Run prediction cycle — called hourly by orchestrator."""
        self._tick_count += 1
        self._init_components()
        print(f"\n[PredAgent] Prediction cycle #{self._tick_count}")

        # 1. Forecast critical metrics
        print(f"  Step 1: Forecasting critical metrics...")
        exhaustion_alerts = self.predict_resource_exhaustion()

        # 2. Check trends
        print(f"  Step 2: Detecting degrading trends...")
        trend_alerts = self._detect_trends()

        # 3. Capacity check (every 6 cycles ≈ every 6 hours)
        capacity_alerts = []
        if self._tick_count % 6 == 1:
            print(f"  Step 3: Running capacity analysis...")
            capacity_alerts = self._check_capacity()

        # 4. Cost check (every 24 cycles ≈ daily)
        if self._tick_count % 24 == 1:
            print(f"  Step 4: Running cost forecast...")
            self._run_cost_forecast()

        total_alerts = len(exhaustion_alerts) + len(trend_alerts) + len(capacity_alerts)
        if total_alerts > 0:
            print(f"  Created {total_alerts} predictive alert(s)")
        else:
            print(f"  No issues predicted — all clear")

    # ── Resource Exhaustion ─────────────────────────────────────────────

    def predict_resource_exhaustion(self) -> List[Dict[str, Any]]:
        """Predict when resources will exhaust for each service."""
        alerts = []
        forecasts = self._forecaster.forecast_all_critical_metrics()

        for service, metric_forecasts in forecasts.items():
            for forecast in metric_forecasts:
                if forecast.get("error"):
                    continue

                anomaly = self._forecaster.detect_anomalies_in_forecast(forecast)
                if anomaly.get("will_breach"):
                    hours = anomaly.get("hours_until_exhaustion")
                    severity = anomaly.get("severity", "low")
                    metric = forecast.get("metric_name", "")

                    if hours is not None and hours < 168:  # 7 days
                        alert_data = {
                            "title": f"Predicted: {metric} exhaustion on {service}",
                            "message": (
                                f"{metric} on {service} predicted to breach threshold "
                                f"in {hours:.0f} hours. Current trend: "
                                f"{forecast.get('trend', {}).get('direction', 'unknown')}."
                            ),
                            "severity": severity,
                            "prediction_type": "resource_exhaustion",
                            "service_name": service,
                            "metric_name": metric,
                            "hours_until_breach": hours,
                            "confidence": 75,
                            "forecasted_date": anomaly.get("first_breach_point", {}).get("ds"),
                        }
                        self._create_predictive_alert(alert_data)
                        alerts.append(alert_data)

                        print(f"    PREDICTION [{severity}]: {metric} on {service} "
                              f"→ breach in {hours:.0f}h")

        return alerts

    # ── Capacity Needs ──────────────────────────────────────────────────

    def predict_capacity_needs(self) -> Dict[str, Any]:
        """Predict when capacity needs to increase."""
        return self._capacity_planner.predict_capacity_breach(days_ahead=30)

    # ── Incident Probability ────────────────────────────────────────────

    def predict_incident_probability(self, service: str) -> Dict[str, Any]:
        """
        Calculate likelihood of an incident in the next few hours.

        Uses trend analysis + forecast breach proximity as signals.
        """
        self._init_components()

        probability = 0.0
        risk_factors = []

        # Check recent trends
        for metric in ["cpu", "memory", "error_rate", "response_time"]:
            forecast = self._forecaster.forecast_metric(service, metric, horizon_hours=6)
            if forecast.get("error"):
                continue

            anomaly = self._forecaster.detect_anomalies_in_forecast(forecast)
            if anomaly.get("will_breach"):
                hours = anomaly.get("hours_until_exhaustion", 100)
                if hours < 6:
                    probability += 30
                    risk_factors.append(f"{metric} breach in {hours:.0f}h")
                elif hours < 12:
                    probability += 15
                    risk_factors.append(f"{metric} trending toward breach")

            trend = forecast.get("trend", {})
            if trend.get("direction") == "increasing" and metric in ("error_rate", "cpu", "memory"):
                probability += 10
                risk_factors.append(f"{metric} increasing")

        probability = min(probability, 100)

        risk_level = "low"
        if probability >= 70:
            risk_level = "critical"
        elif probability >= 50:
            risk_level = "high"
        elif probability >= 30:
            risk_level = "medium"

        return {
            "service": service,
            "probability": round(probability, 1),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "message": (
                f"High risk of incident on {service} in next 4 hours"
                if probability >= 50
                else f"Low risk on {service}"
            ),
            "predicted_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Traffic Spike Prediction ────────────────────────────────────────

    def predict_traffic_spike(self) -> List[Dict[str, Any]]:
        """Forecast traffic spikes that may exceed capacity."""
        self._init_components()
        alerts = []

        services = self._forecaster._get_active_services()
        for svc in services:
            forecast = self._forecaster.forecast_metric(svc, "response_time", 24)
            if forecast.get("error"):
                continue

            trend = forecast.get("trend", {})
            if trend.get("direction") == "increasing":
                change = trend.get("change_over_horizon", 0)
                if change > 100:  # >100ms increase predicted
                    alerts.append({
                        "service": svc,
                        "type": "traffic_spike",
                        "predicted_increase_ms": round(change, 1),
                        "message": f"Response time on {svc} predicted to increase by {change:.0f}ms",
                    })

        return alerts

    # ── Cost Forecast ───────────────────────────────────────────────────

    def forecast_costs(self) -> Dict[str, Any]:
        """Predict infrastructure costs for the next month."""
        self._init_components()
        return self._cost_forecaster.forecast_monthly_cost()

    # ── Internal Helpers ────────────────────────────────────────────────

    def _detect_trends(self) -> List[dict]:
        """Run trend detection across services."""
        alerts = []
        services = self._forecaster._get_active_services()

        for svc in services[:5]:  # Limit to avoid slow cycles
            trends = self._trend_detector.detect_degrading_trends(svc)
            for trend in trends:
                if trend.get("severity") in ("high", "critical"):
                    alert_data = {
                        "title": f"Degrading trend: {trend['metric']} on {svc}",
                        "message": trend.get("description", ""),
                        "severity": trend["severity"],
                        "prediction_type": "degrading_trend",
                        "service_name": svc,
                        "metric_name": trend["metric"],
                        "confidence": trend.get("confidence", 60),
                    }
                    self._create_predictive_alert(alert_data)
                    alerts.append(alert_data)
        return alerts

    def _check_capacity(self) -> List[dict]:
        """Run capacity planning checks."""
        alerts = []
        breach = self._capacity_planner.predict_capacity_breach(days_ahead=30)

        for svc, info in breach.get("services", {}).items():
            if info.get("will_breach"):
                days = info.get("days_until_breach", 999)
                if days < 30:
                    severity = "critical" if days < 7 else "high" if days < 14 else "medium"
                    alert_data = {
                        "title": f"Capacity breach: {svc} in {days} days",
                        "message": (
                            f"{info.get('metric', 'resource')} on {svc} "
                            f"will exceed capacity in {days} days. "
                            f"Recommendation: {info.get('recommendation', 'scale up')}"
                        ),
                        "severity": severity,
                        "prediction_type": "capacity_breach",
                        "service_name": svc,
                        "confidence": info.get("confidence", 60),
                        "forecasted_date": info.get("breach_date"),
                    }
                    self._create_predictive_alert(alert_data)
                    alerts.append(alert_data)
        return alerts

    def _run_cost_forecast(self):
        """Generate and store cost forecast."""
        try:
            forecast = self._cost_forecaster.forecast_monthly_cost()
            if forecast.get("predicted_total", 0) > 0:
                current = forecast.get("current_monthly", 0)
                predicted = forecast.get("predicted_total", 0)
                if predicted > current * 1.3:  # >30% increase
                    self._create_predictive_alert({
                        "title": "Cost overrun predicted",
                        "message": (
                            f"Next month's cost predicted at ${predicted:.0f} "
                            f"(current: ${current:.0f}, +{((predicted/current - 1) * 100):.0f}%)"
                        ),
                        "severity": "medium",
                        "prediction_type": "cost_overrun",
                        "confidence": 65,
                    })
        except Exception as e:
            logger.debug(f"Cost forecast failed: {e}")

    def _create_predictive_alert(self, alert_data: dict):
        """Create a predictive alert via the backend API."""
        try:
            self.api_post("/alerts/predictive", alert_data)
        except Exception:
            # Fall back to regular alert endpoint
            try:
                self.api_post("/alerts/", {
                    "title": f"[PREDICTED] {alert_data.get('title', '')}",
                    "message": alert_data.get("message", ""),
                    "severity": alert_data.get("severity", "low"),
                })
            except Exception as e:
                logger.debug(f"Failed to create predictive alert: {e}")
