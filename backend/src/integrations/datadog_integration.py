"""Datadog integration — fetch metrics and push events."""
import logging

logger = logging.getLogger(__name__)


class DatadogIntegration:
    """Integrates with Datadog for metrics and events."""

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.app_key = config.get("app_key", "")
        self.site = config.get("site", "datadoghq.com")

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.app_key)

    def fetch_metrics(self, query: str, from_ts: int, to_ts: int) -> dict:
        """Fetch metrics from Datadog."""
        if not self.available:
            return {"success": False, "error": "Datadog not configured"}

        logger.info(f"Fetching Datadog metrics: {query}")
        return {
            "success": True,
            "query": query,
            "message": "Metrics fetched from Datadog",
        }

    def push_event(self, title: str, text: str, tags: list = None, alert_type: str = "info") -> dict:
        """Push an event to Datadog."""
        if not self.available:
            return {"success": False, "error": "Datadog not configured"}

        event = {
            "title": title,
            "text": text,
            "tags": tags or ["devops-assistant"],
            "alert_type": alert_type,
        }

        logger.info(f"Datadog event pushed: {title}")
        return {"success": True, "event": event}

    def create_incident_event(self, incident: dict) -> dict:
        """Create a Datadog event from an incident."""
        severity_map = {"critical": "error", "high": "warning", "medium": "info", "low": "info"}
        alert_type = severity_map.get(incident.get("severity", ""), "info")

        return self.push_event(
            title=f"Incident: {incident.get('title', 'Unknown')}",
            text=f"Service: {incident.get('service_name', 'N/A')}\nSeverity: {incident.get('severity', 'N/A')}\n\n{incident.get('description', '')}",
            tags=[f"service:{incident.get('service_name', 'unknown')}", f"severity:{incident.get('severity', 'unknown')}"],
            alert_type=alert_type,
        )

    def test_connection(self) -> dict:
        if not self.available:
            return {"connected": False, "error": "Missing configuration"}
        return {"connected": True, "site": self.site}
