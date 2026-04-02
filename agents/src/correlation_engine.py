"""
Correlation Engine: Links incidents with potential causes by analyzing
deployments, metric spikes, time patterns, and service dependencies.
"""
from datetime import datetime, timedelta
from typing import List, Optional


# Known service dependencies
SERVICE_DEPENDENCIES = {
    "api-gateway": ["auth-service", "web-server-01"],
    "web-server-01": ["database-primary", "cache-redis"],
    "auth-service": ["database-primary", "cache-redis"],
}


class CorrelationEngine:
    def __init__(self, api_get_fn):
        """api_get_fn: function to call backend API (e.g. agent.api_get)"""
        self._get = api_get_fn

    def correlate_incident(self, incident: dict) -> dict:
        """
        Analyze an incident and find correlated events.
        Returns correlation results with scores.
        """
        service = incident.get("service_name", "")
        detected_at = incident.get("detected_at", "")

        correlations = []
        total_score = 0

        # 1. Deployment correlation
        deploy_corr = self._check_deployments(service, detected_at)
        if deploy_corr:
            correlations.append(deploy_corr)
            total_score = max(total_score, deploy_corr["score"])

        # 2. Metric correlation
        metric_corr = self._check_metric_spikes(service, detected_at)
        if metric_corr:
            correlations.append(metric_corr)
            total_score = max(total_score, metric_corr["score"])

        # 3. Cascading failure correlation
        cascade_corr = self._check_cascading_failures(service, detected_at)
        if cascade_corr:
            correlations.append(cascade_corr)
            total_score = max(total_score, cascade_corr["score"])

        # 4. Time correlation (multiple incidents around same time)
        time_corr = self._check_time_correlation(detected_at)
        if time_corr:
            correlations.append(time_corr)
            total_score = max(total_score, time_corr["score"])

        return {
            "incident_id": incident.get("id"),
            "correlations": correlations,
            "max_score": total_score,
            "likely_cause": self._determine_likely_cause(correlations),
        }

    def _check_deployments(self, service: str, detected_at: str) -> Optional[dict]:
        """Check for recent deployments (within 30 min of incident)."""
        try:
            deployments = self._get("/deployments/recent", {"hours": 1})
            if not deployments:
                return None

            for dep in deployments:
                dep_time = dep.get("deployed_at", "")
                dep_service = dep.get("service_name", "")

                # Check if deployment was for affected service or its dependencies
                related = (dep_service == service or
                           dep_service in SERVICE_DEPENDENCIES.get(service, []))

                if related:
                    return {
                        "type": "deployment",
                        "score": 90,
                        "description": f"Deployment of {dep_service} v{dep.get('version', '?')} "
                                       f"occurred at {dep_time}",
                        "data": dep
                    }
        except Exception as e:
            print(f"  [CORR] Deployment check failed: {e}")
        return None

    def _check_metric_spikes(self, service: str, detected_at: str) -> Optional[dict]:
        """Check for metric spikes before the incident."""
        try:
            metrics = self._get("/metrics/", {
                "service_name": service,
                "hours": 1,
                "limit": 50
            })
            if not metrics:
                return None

            # Find abnormal values
            spikes = []
            for m in metrics:
                name = m.get("metric_name", "")
                val = m.get("value", 0)
                if (name == "cpu" and val > 80) or \
                   (name == "memory" and val > 85) or \
                   (name == "error_rate" and val > 5) or \
                   (name == "response_time" and val > 500):
                    spikes.append(f"{name}={val:.1f}")

            if spikes:
                return {
                    "type": "metric_spike",
                    "score": 75,
                    "description": f"Metric spikes detected on {service}: {', '.join(spikes[:5])}",
                    "data": {"spikes": spikes}
                }
        except Exception as e:
            print(f"  [CORR] Metric check failed: {e}")
        return None

    def _check_cascading_failures(self, service: str, detected_at: str) -> Optional[dict]:
        """Check if dependent services are also having issues."""
        deps = SERVICE_DEPENDENCIES.get(service, [])
        if not deps:
            return None

        try:
            affected_deps = []
            for dep_service in deps:
                alerts = self._get("/alerts/", {
                    "limit": 5,
                    "resolved": False
                })
                for alert in (alerts or []):
                    if dep_service in alert.get("title", ""):
                        affected_deps.append(dep_service)
                        break

            if affected_deps:
                return {
                    "type": "cascading_failure",
                    "score": 85,
                    "description": f"Dependent services also affected: {', '.join(affected_deps)}",
                    "data": {"affected_services": affected_deps}
                }
        except Exception as e:
            print(f"  [CORR] Cascade check failed: {e}")
        return None

    def _check_time_correlation(self, detected_at: str) -> Optional[dict]:
        """Check for multiple incidents around the same time."""
        try:
            # Get recent open incidents
            incidents = self._get("/incidents/", {"status": "open", "limit": 10})
            if incidents and len(incidents) > 1:
                return {
                    "type": "time_correlation",
                    "score": 65,
                    "description": f"{len(incidents)} incidents open simultaneously",
                    "data": {"open_count": len(incidents)}
                }
        except Exception as e:
            print(f"  [CORR] Time check failed: {e}")
        return None

    def _determine_likely_cause(self, correlations: list) -> str:
        if not correlations:
            return "No correlations found"

        best = max(correlations, key=lambda c: c["score"])
        if best["score"] >= 90:
            return f"Very likely: {best['description']}"
        elif best["score"] >= 70:
            return f"Probably: {best['description']}"
        elif best["score"] >= 50:
            return f"Possibly: {best['description']}"
        return f"Uncertain: {best['description']}"
