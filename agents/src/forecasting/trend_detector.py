"""
Trend Detector: Identifies degrading performance trends before they
become incidents — catches the "slow boil" phase.
Uses linear regression, moving averages, and statistical tests.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

import numpy as np

logger = logging.getLogger(__name__)


class TrendDetector:
    """Detects gradual metric degradation and correlates trends."""

    # How much change per day triggers alerts
    TREND_THRESHOLDS = {
        "cpu": {"warn": 2.0, "critical": 5.0},        # % per day
        "memory": {"warn": 2.0, "critical": 5.0},      # % per day
        "error_rate": {"warn": 0.5, "critical": 2.0},   # errors/min per day
        "response_time": {"warn": 20, "critical": 50},   # ms per day
    }

    def __init__(self, api_get=None):
        self._api_get = api_get

    def detect_degrading_trends(self, service: str) -> List[Dict[str, Any]]:
        """
        Analyze all metrics for a service and identify degrading trends.

        Returns list of trends with severity, rate of change, and predictions.
        """
        trends = []

        for metric in ["cpu", "memory", "error_rate", "response_time"]:
            values = self._fetch_metric_values(service, metric, hours=168)  # 7 days
            if len(values) < 20:
                continue

            analysis = self._analyze_trend(values, metric)
            if analysis.get("is_degrading"):
                thresholds = self.TREND_THRESHOLDS.get(metric, {})
                rate = abs(analysis.get("rate_per_day", 0))

                if rate >= thresholds.get("critical", 999):
                    severity = "critical"
                elif rate >= thresholds.get("warn", 999):
                    severity = "high"
                else:
                    severity = "medium"

                trends.append({
                    "service": service,
                    "metric": metric,
                    "severity": severity,
                    "direction": analysis["direction"],
                    "rate_per_day": round(analysis["rate_per_day"], 3),
                    "rate_description": (
                        f"{metric} {'increasing' if analysis['direction'] == 'up' else 'decreasing'} "
                        f"by {rate:.1f} per day"
                    ),
                    "description": (
                        f"{metric} on {service} is {analysis['direction']} "
                        f"at {rate:.1f}/day — predicted issue in "
                        f"{analysis.get('days_until_issue', '?')} days"
                    ),
                    "current_value": round(analysis.get("current_value", 0), 2),
                    "predicted_value_7d": round(analysis.get("predicted_7d", 0), 2),
                    "confidence": analysis.get("confidence", 50),
                    "days_until_issue": analysis.get("days_until_issue"),
                })

        return trends

    def predict_future_anomaly(
        self, service: str, metric: str, days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Predict when a metric will become anomalous based on current trend.
        """
        values = self._fetch_metric_values(service, metric, hours=168)
        if len(values) < 20:
            return {"error": "Insufficient data", "data_points": len(values)}

        analysis = self._analyze_trend(values, metric)

        from .prophet_forecaster import ProphetForecaster
        thresholds = ProphetForecaster.THRESHOLDS
        threshold = thresholds.get(metric, 100)

        current = analysis.get("current_value", 0)
        rate = analysis.get("rate_per_day", 0)

        days_until = None
        if rate > 0:
            remaining = threshold - current
            if remaining > 0:
                days_until = remaining / rate
            elif remaining <= 0:
                days_until = 0  # already breached

        return {
            "service": service,
            "metric": metric,
            "current_value": round(current, 2),
            "threshold": threshold,
            "rate_per_day": round(rate, 3),
            "days_until_anomaly": round(days_until, 1) if days_until is not None else None,
            "will_become_anomalous": days_until is not None and days_until <= days_ahead,
            "confidence": analysis.get("confidence", 50),
        }

    def identify_seasonal_anomalies(
        self, service: str, metric: str
    ) -> Dict[str, Any]:
        """
        Detect deviations from normal seasonal patterns.

        Compares current values to expected values based on time-of-day/day-of-week.
        """
        values_with_ts = self._fetch_metric_with_timestamps(service, metric, hours=168)
        if len(values_with_ts) < 48:
            return {"error": "Insufficient data"}

        # Build hourly baselines (average by hour-of-day)
        hourly_baselines = {}
        for ts_str, value in values_with_ts:
            try:
                dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00").replace("+00:00", ""))
                hour = dt.hour
                if hour not in hourly_baselines:
                    hourly_baselines[hour] = []
                hourly_baselines[hour].append(float(value))
            except (ValueError, TypeError):
                continue

        hourly_means = {h: np.mean(v) for h, v in hourly_baselines.items()}
        hourly_stds = {h: np.std(v) for h, v in hourly_baselines.items()}

        # Check recent values against baseline
        anomalies = []
        recent = values_with_ts[-24:]  # last 24 points
        for ts_str, value in recent:
            try:
                dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00").replace("+00:00", ""))
                hour = dt.hour
                mean = hourly_means.get(hour, 0)
                std = hourly_stds.get(hour, 1)
                if std > 0:
                    z_score = abs(float(value) - mean) / std
                    if z_score > 2.5:
                        anomalies.append({
                            "timestamp": ts_str,
                            "value": float(value),
                            "expected": round(mean, 2),
                            "z_score": round(z_score, 2),
                            "direction": "above" if float(value) > mean else "below",
                        })
            except (ValueError, TypeError):
                continue

        return {
            "service": service,
            "metric": metric,
            "seasonal_anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "hourly_baselines": {h: round(v, 2) for h, v in hourly_means.items()},
        }

    def correlate_trends(self, service: str) -> List[Dict[str, Any]]:
        """
        Find metrics trending in the same direction on the same service.
        """
        metric_trends = {}
        for metric in ["cpu", "memory", "error_rate", "response_time"]:
            values = self._fetch_metric_values(service, metric, hours=168)
            if len(values) >= 20:
                analysis = self._analyze_trend(values, metric)
                metric_trends[metric] = analysis

        # Find correlated trends (same direction)
        correlations = []
        metrics = list(metric_trends.keys())
        for i in range(len(metrics)):
            for j in range(i + 1, len(metrics)):
                a = metric_trends[metrics[i]]
                b = metric_trends[metrics[j]]

                if a["direction"] == b["direction"] and a["direction"] != "stable":
                    correlations.append({
                        "metrics": [metrics[i], metrics[j]],
                        "direction": a["direction"],
                        "description": (
                            f"{metrics[i]} and {metrics[j]} both {a['direction']} — "
                            f"likely shared root cause"
                        ),
                        "combined_severity": max(
                            abs(a.get("rate_per_day", 0)),
                            abs(b.get("rate_per_day", 0)),
                        ),
                    })

        return sorted(correlations, key=lambda x: x["combined_severity"], reverse=True)

    # ── Analysis Methods ────────────────────────────────────────────────

    def _analyze_trend(self, values: List[float], metric: str) -> dict:
        """
        Analyze trend using linear regression and moving averages.
        """
        n = len(values)
        x = np.arange(n, dtype=float)
        y = np.array(values, dtype=float)

        # Linear regression
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        denom = np.sum((x - x_mean) ** 2)
        if denom == 0:
            return {"direction": "stable", "is_degrading": False, "confidence": 0}

        slope = np.sum((x - x_mean) * (y - y_mean)) / denom

        # R-squared for confidence
        y_pred = slope * x + (y_mean - slope * x_mean)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Convert slope to "per day" (assume ~1 point per hour)
        rate_per_day = slope * 24

        # Moving average comparison (last 24h avg vs previous 24h)
        if n >= 48:
            recent_avg = np.mean(y[-24:])
            previous_avg = np.mean(y[-48:-24])
            ma_change = recent_avg - previous_avg
        else:
            recent_avg = np.mean(y[-n // 2:])
            previous_avg = np.mean(y[:n // 2])
            ma_change = recent_avg - previous_avg

        # Determine direction
        is_increasing = rate_per_day > 0.1 and ma_change > 0
        is_decreasing = rate_per_day < -0.1 and ma_change < 0

        if is_increasing:
            direction = "up"
        elif is_decreasing:
            direction = "down"
        else:
            direction = "stable"

        # Is it degrading? (increasing for cpu/memory/errors, or decreasing for throughput)
        bad_metrics = {"cpu", "memory", "error_rate", "response_time"}
        is_degrading = (metric in bad_metrics and is_increasing)

        # Predict days until threshold
        from .prophet_forecaster import ProphetForecaster
        threshold = ProphetForecaster.THRESHOLDS.get(metric, 100)
        current_value = float(y[-1])
        days_until_issue = None
        if rate_per_day > 0:
            remaining = threshold - current_value
            if remaining > 0:
                days_until_issue = round(remaining / rate_per_day, 1)

        return {
            "direction": direction,
            "is_degrading": is_degrading,
            "rate_per_day": round(float(rate_per_day), 4),
            "r_squared": round(float(max(0, r_squared)), 3),
            "confidence": round(float(max(0, r_squared)) * 100, 1),
            "current_value": round(float(current_value), 2),
            "moving_avg_change": round(float(ma_change), 2),
            "predicted_7d": round(float(current_value + rate_per_day * 7), 2),
            "days_until_issue": days_until_issue,
        }

    # ── Data Fetching ───────────────────────────────────────────────────

    def _fetch_metric_values(
        self, service: str, metric: str, hours: int
    ) -> List[float]:
        """Fetch metric values as a flat list of floats."""
        if not self._api_get:
            return self._synthetic_values(hours)

        try:
            data = self._api_get("/metrics/", {
                "service_name": service,
                "metric_name": metric,
                "hours": hours,
                "limit": 2000,
            })
            return [float(m.get("value", 0)) for m in data]
        except Exception:
            return []

    def _fetch_metric_with_timestamps(
        self, service: str, metric: str, hours: int
    ) -> List[list]:
        """Fetch metric values with timestamps."""
        if not self._api_get:
            now = datetime.now(timezone.utc)
            return [
                [(now - timedelta(hours=h)).isoformat(), v]
                for h, v in enumerate(self._synthetic_values(hours))
            ]

        try:
            data = self._api_get("/metrics/", {
                "service_name": service,
                "metric_name": metric,
                "hours": hours,
                "limit": 2000,
            })
            return [[m.get("recorded_at", ""), m.get("value", 0)] for m in data]
        except Exception:
            return []

    def _synthetic_values(self, hours: int) -> List[float]:
        """Generate synthetic metric data for testing."""
        t = np.arange(hours, dtype=float)
        # Upward trend + daily seasonality + noise
        base = 45 + 0.05 * t
        seasonal = 10 * np.sin(2 * np.pi * t / 24)
        noise = np.random.normal(0, 2, hours)
        return (base + seasonal + noise).tolist()
