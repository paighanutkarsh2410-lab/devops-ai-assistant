"""
Monitor Agent: Collects metrics from Prometheus, detects anomalies, creates alerts.
"""
import requests
from datetime import datetime
from base_agent import BaseAgent
from anomaly_detector import AnomalyDetector
from config import PROMETHEUS_URL, ANOMALY_THRESHOLD

# Prometheus queries for each metric type
PROM_QUERIES = {
    "cpu": 'service_cpu_percent',
    "memory": 'service_memory_percent',
    "error_rate": 'service_error_rate',
    "response_time": 'service_response_time_ms',
}


class MonitorAgent(BaseAgent):
    def __init__(self):
        super().__init__("MonitorAgent")
        self.detector = AnomalyDetector(z_threshold=ANOMALY_THRESHOLD)
        self._tick_count = 0

    def tick(self):
        """Collect metrics from Prometheus, analyze, store, and alert."""
        self._tick_count += 1
        print(f"\n[{self.name}] Tick #{self._tick_count} at {datetime.utcnow().isoformat()}")

        metrics_collected = []
        anomalies = []

        for metric_name, query in PROM_QUERIES.items():
            try:
                values = self._query_prometheus(query)
                for service, value in values.items():
                    metrics_collected.append({
                        "service_name": service,
                        "metric_name": metric_name,
                        "value": round(value, 2),
                        "unit": self._get_unit(metric_name),
                    })

                    # Check for anomalies
                    anomaly = self.detector.detect(service, metric_name, value)
                    if anomaly:
                        anomalies.append(anomaly)

            except Exception as e:
                print(f"  [WARN] Failed to query {metric_name}: {e}")

        # Store metrics in bulk
        if metrics_collected:
            try:
                result = self.api_post("/metrics/bulk", {"metrics": metrics_collected})
                print(f"  Stored {result['inserted']} metrics")
            except Exception as e:
                print(f"  [WARN] Failed to store metrics: {e}")

        # Process anomalies
        for anomaly in anomalies:
            self._handle_anomaly(anomaly)

        if not anomalies:
            print(f"  All systems normal ({len(metrics_collected)} metrics collected)")

    def _query_prometheus(self, query: str) -> dict:
        """Query Prometheus and return {service_name: value} dict."""
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()

        results = {}
        for item in data.get("data", {}).get("result", []):
            service = item["metric"].get("service", "unknown")
            value = float(item["value"][1])
            results[service] = value

        return results

    def _handle_anomaly(self, anomaly: dict):
        """Create an alert for a detected anomaly."""
        svc = anomaly["service"]
        metric = anomaly["metric"]
        val = anomaly["value"]
        severity = anomaly["severity"]
        methods = ", ".join(anomaly["methods"])
        baseline = anomaly["baseline_avg"]

        title = f"{severity.upper()}: {metric} anomaly on {svc}"
        message = (
            f"{metric} on {svc} is {val:.1f} (baseline: {baseline:.1f}). "
            f"Detected by: {methods}. Score: {anomaly['score']:.2f}"
        )

        print(f"  ANOMALY [{severity}] {title}")
        print(f"    {message}")

        try:
            self.api_post("/alerts/", {
                "title": title,
                "message": message,
                "severity": severity,
            })
            print(f"    Alert created successfully")
        except Exception as e:
            print(f"    [WARN] Failed to create alert: {e}")

    def _get_unit(self, metric_name: str) -> str:
        units = {
            "cpu": "%",
            "memory": "%",
            "error_rate": "err/min",
            "response_time": "ms",
        }
        return units.get(metric_name, "")
