"""
Metric Collector: Collects real-time metrics from backend API or Prometheus.
"""
import logging

logger = logging.getLogger(__name__)


class MetricCollector:
    """Collects service metrics for impact analysis."""

    def __init__(self, api_get_fn=None):
        self._api_get = api_get_fn

    def collect_snapshot(self, service: str) -> dict:
        """Collect a snapshot of key metrics for a service."""
        if not self._api_get:
            return {}

        snapshot = {}
        try:
            metrics = self._api_get("/metrics/", {
                "service_name": service,
                "hours": 0.1,
                "limit": 20,
            })
            for m in (metrics or []):
                name = m.get("metric_name", "")
                value = m.get("value", 0)
                # Keep latest value for each metric
                if name not in snapshot:
                    snapshot[name] = value
        except Exception as e:
            logger.warning(f"[Collector] Failed to collect metrics for {service}: {e}")

        return snapshot

    def collect_baseline(self, service: str, duration_hours: float = 1.0) -> dict:
        """Collect baseline averages over a time period."""
        if not self._api_get:
            return {}

        try:
            agg = self._api_get("/metrics/aggregations", {
                "service_name": service,
                "metric_name": "cpu",
                "hours": duration_hours,
            })
            baseline = {"cpu": agg.get("avg", 0)}

            for metric in ["memory", "response_time", "error_rate"]:
                try:
                    agg = self._api_get("/metrics/aggregations", {
                        "service_name": service,
                        "metric_name": metric,
                        "hours": duration_hours,
                    })
                    baseline[metric] = agg.get("avg", 0)
                except Exception:
                    pass

            return baseline
        except Exception as e:
            logger.warning(f"[Collector] Failed to collect baseline for {service}: {e}")
            return {}
