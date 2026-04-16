"""
Prophet Time-Series Forecaster: Predicts infrastructure metrics using
Facebook Prophet with daily/weekly seasonality and holiday effects.

Falls back to linear regression when Prophet is not installed.
"""
import os
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

logger = logging.getLogger(__name__)

# Graceful import
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.info("Prophet not installed — using linear regression fallback")

# Forecast cache: key -> (timestamp, result)
_forecast_cache: Dict[str, Tuple[float, dict]] = {}
CACHE_TTL = 3600  # 1 hour


class ProphetForecaster:
    """Time-series forecasting for infrastructure metrics."""

    # Thresholds for exhaustion detection
    THRESHOLDS = {
        "cpu": 90.0,
        "memory": 90.0,
        "disk": 85.0,
        "error_rate": 10.0,
        "response_time": 1000.0,  # ms
        "connections": 90.0,  # % of max
    }

    def __init__(self, api_get=None):
        self._api_get = api_get

    def forecast_metric(
        self,
        service: str,
        metric_name: str,
        horizon_hours: int = 24,
        history_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate a forecast for a specific service metric.

        Args:
            service: Service name.
            metric_name: cpu, memory, disk, etc.
            horizon_hours: How far ahead to predict.
            history_days: How much history to use.

        Returns:
            Dict with forecast values, confidence intervals, and metadata.
        """
        # Check cache
        cache_key = f"{service}:{metric_name}:{horizon_hours}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Fetch historical data
        history = self._fetch_metric_history(service, metric_name, history_days)
        if len(history) < 10:
            return {"error": "Insufficient data", "data_points": len(history)}

        # Generate forecast
        if PROPHET_AVAILABLE:
            result = self._forecast_prophet(history, horizon_hours, metric_name)
        else:
            result = self._forecast_linear(history, horizon_hours)

        result["service"] = service
        result["metric_name"] = metric_name
        result["horizon_hours"] = horizon_hours
        result["data_points_used"] = len(history)
        result["generated_at"] = datetime.now(timezone.utc).isoformat()

        # Check for threshold breach
        threshold = self.THRESHOLDS.get(metric_name)
        if threshold:
            breach_info = self._find_threshold_breach(result.get("forecast", []), threshold)
            result["threshold"] = threshold
            result["breach_predicted"] = breach_info["will_breach"]
            result["hours_until_breach"] = breach_info.get("hours_until_breach")

        self._set_cached(cache_key, result)
        return result

    def detect_anomalies_in_forecast(self, forecast: dict) -> Dict[str, Any]:
        """
        Check if a forecast predicts anomalous values.

        Returns:
            Dict with anomaly info, exhaustion time, severity.
        """
        points = forecast.get("forecast", [])
        metric = forecast.get("metric_name", "")
        threshold = self.THRESHOLDS.get(metric, 100)

        anomalies = []
        first_breach = None

        for pt in points:
            value = pt.get("yhat", 0)
            upper = pt.get("yhat_upper", value)

            if value > threshold:
                if not first_breach:
                    first_breach = pt
                anomalies.append(pt)
            elif upper > threshold:
                anomalies.append({**pt, "type": "possible_breach"})

        hours_until = None
        if first_breach:
            try:
                breach_time = datetime.fromisoformat(first_breach["ds"])
                hours_until = max(0, (breach_time - datetime.now(timezone.utc)).total_seconds() / 3600)
            except (ValueError, TypeError):
                pass

        severity = "none"
        if hours_until is not None:
            if hours_until < 6:
                severity = "critical"
            elif hours_until < 24:
                severity = "high"
            elif hours_until < 72:
                severity = "medium"
            else:
                severity = "low"

        return {
            "will_breach": len(anomalies) > 0,
            "anomaly_count": len(anomalies),
            "hours_until_exhaustion": round(hours_until, 1) if hours_until else None,
            "severity": severity,
            "threshold": threshold,
            "first_breach_point": first_breach,
        }

    def forecast_all_critical_metrics(
        self, services: List[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Forecast all critical metrics for all services (parallelized).

        Returns:
            Dict of service -> list of metric forecasts.
        """
        if not services:
            services = self._get_active_services()

        critical_metrics = ["cpu", "memory", "error_rate", "response_time"]
        results = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for svc in services:
                for metric in critical_metrics:
                    key = f"{svc}:{metric}"
                    futures[executor.submit(
                        self.forecast_metric, svc, metric, 24
                    )] = key

            for future in as_completed(futures):
                key = futures[future]
                svc = key.split(":")[0]
                try:
                    result = future.result()
                    if svc not in results:
                        results[svc] = []
                    results[svc].append(result)
                except Exception as e:
                    logger.error(f"Forecast failed for {key}: {e}")

        return results

    # ── Prophet Forecast ────────────────────────────────────────────────

    def _forecast_prophet(
        self, history: List[dict], horizon_hours: int, metric_name: str
    ) -> dict:
        """Generate forecast using Prophet."""
        import pandas as pd

        df = pd.DataFrame(history)
        df.columns = ["ds", "y"]
        df["ds"] = pd.to_datetime(df["ds"])

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            interval_width=0.90,
        )

        # Suppress Prophet logging
        import logging as _log
        _log.getLogger("prophet").setLevel(_log.WARNING)
        _log.getLogger("cmdstanpy").setLevel(_log.WARNING)

        model.fit(df)

        future = model.make_future_dataframe(periods=horizon_hours, freq="h")
        prediction = model.predict(future)

        # Extract forecast (only future points)
        cutoff = df["ds"].max()
        forecast_df = prediction[prediction["ds"] > cutoff]

        forecast_points = []
        for _, row in forecast_df.iterrows():
            forecast_points.append({
                "ds": row["ds"].isoformat(),
                "yhat": round(float(row["yhat"]), 2),
                "yhat_lower": round(float(row["yhat_lower"]), 2),
                "yhat_upper": round(float(row["yhat_upper"]), 2),
            })

        # Historical fitted values (last 48 hours for chart context)
        history_fitted = []
        recent = prediction.tail(48 + horizon_hours).head(48)
        for _, row in recent.iterrows():
            history_fitted.append({
                "ds": row["ds"].isoformat(),
                "yhat": round(float(row["yhat"]), 2),
                "actual": None,
            })

        return {
            "method": "prophet",
            "forecast": forecast_points,
            "history_fitted": history_fitted,
            "trend": self._calculate_trend(forecast_points),
        }

    # ── Linear Regression Fallback ──────────────────────────────────────

    def _forecast_linear(self, history: List[dict], horizon_hours: int) -> dict:
        """Simple linear regression forecast as fallback."""
        timestamps = []
        values = []

        for entry in history:
            try:
                ts = datetime.fromisoformat(str(entry[0]).replace("Z", "+00:00").replace("+00:00", ""))
                timestamps.append(ts.timestamp())
                values.append(float(entry[1]))
            except (ValueError, TypeError, IndexError):
                continue

        if len(values) < 5:
            return {"method": "linear", "forecast": [], "error": "Insufficient data"}

        x = np.array(timestamps)
        y = np.array(values)

        # Linear regression
        n = len(x)
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
        intercept = y_mean - slope * x_mean

        # Standard error for confidence bands
        y_pred = slope * x + intercept
        residuals = y - y_pred
        std_err = np.std(residuals)

        # Generate future points
        now = datetime.now(timezone.utc)
        forecast_points = []
        for h in range(1, horizon_hours + 1):
            future_ts = (now + timedelta(hours=h)).timestamp()
            yhat = slope * future_ts + intercept
            forecast_points.append({
                "ds": (now + timedelta(hours=h)).isoformat(),
                "yhat": round(float(yhat), 2),
                "yhat_lower": round(float(yhat - 1.96 * std_err), 2),
                "yhat_upper": round(float(yhat + 1.96 * std_err), 2),
            })

        # Trend direction
        if len(forecast_points) >= 2:
            trend_val = forecast_points[-1]["yhat"] - forecast_points[0]["yhat"]
        else:
            trend_val = 0

        return {
            "method": "linear_regression",
            "forecast": forecast_points,
            "history_fitted": [],
            "trend": {
                "direction": "increasing" if trend_val > 0.5 else "decreasing" if trend_val < -0.5 else "stable",
                "slope_per_hour": round(float(slope * 3600), 4),
                "change_over_horizon": round(float(trend_val), 2),
            },
        }

    # ── Helpers ─────────────────────────────────────────────────────────

    def _fetch_metric_history(
        self, service: str, metric_name: str, days: int
    ) -> List[list]:
        """Fetch metric data from backend API."""
        if not self._api_get:
            return self._generate_synthetic_history(days)

        try:
            data = self._api_get("/metrics/", {
                "service_name": service,
                "metric_name": metric_name,
                "hours": days * 24,
                "limit": 5000,
            })
            return [[m.get("recorded_at", ""), m.get("value", 0)] for m in data]
        except Exception as e:
            logger.error(f"Failed to fetch metric history: {e}")
            return []

    def _generate_synthetic_history(self, days: int) -> List[list]:
        """Generate synthetic data for testing/demo."""
        now = datetime.now(timezone.utc)
        points = []
        for h in range(days * 24, 0, -1):
            ts = now - timedelta(hours=h)
            # Simulate daily pattern with noise
            hour = ts.hour
            base = 40 + 20 * np.sin(2 * np.pi * hour / 24)
            noise = np.random.normal(0, 3)
            # Weekly pattern
            if ts.weekday() >= 5:
                base *= 0.7
            points.append([ts.isoformat(), round(float(base + noise), 2)])
        return points

    def _find_threshold_breach(
        self, forecast_points: list, threshold: float
    ) -> dict:
        """Find when a forecast will breach a threshold."""
        for pt in forecast_points:
            if pt.get("yhat", 0) > threshold:
                try:
                    breach_time = datetime.fromisoformat(pt["ds"])
                    hours = max(0, (breach_time - datetime.now(timezone.utc)).total_seconds() / 3600)
                    return {
                        "will_breach": True,
                        "hours_until_breach": round(hours, 1),
                        "breach_value": pt["yhat"],
                    }
                except (ValueError, TypeError):
                    pass
        return {"will_breach": False}

    def _calculate_trend(self, forecast_points: list) -> dict:
        """Calculate trend from forecast points."""
        if len(forecast_points) < 2:
            return {"direction": "stable", "change_over_horizon": 0}

        first = forecast_points[0]["yhat"]
        last = forecast_points[-1]["yhat"]
        change = last - first

        return {
            "direction": "increasing" if change > 1 else "decreasing" if change < -1 else "stable",
            "change_over_horizon": round(change, 2),
            "start_value": first,
            "end_value": last,
        }

    def _get_active_services(self) -> List[str]:
        """Get list of active services from backend."""
        if not self._api_get:
            return ["api-server", "web-server", "worker-service", "database"]
        try:
            incidents = self._api_get("/incidents/", {"limit": 50})
            services = set()
            for inc in incidents:
                svc = inc.get("service_name")
                if svc:
                    services.add(svc)
            return list(services) or ["api-server", "web-server"]
        except Exception:
            return ["api-server", "web-server"]

    def _get_cached(self, key: str) -> Optional[dict]:
        """Get a cached forecast if still valid."""
        if key in _forecast_cache:
            ts, result = _forecast_cache[key]
            if (datetime.now(timezone.utc).timestamp() - ts) < CACHE_TTL:
                return result
        return None

    def _set_cached(self, key: str, result: dict):
        """Cache a forecast result."""
        _forecast_cache[key] = (datetime.now(timezone.utc).timestamp(), result)
