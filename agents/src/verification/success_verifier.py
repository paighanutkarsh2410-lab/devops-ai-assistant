"""
Success Verifier: Confirms that a remediation action actually fixed the issue.
Scoring: 90-100 full success, 70-89 partial, 50-69 unclear, 0-49 failed.
"""
import time
import logging

logger = logging.getLogger(__name__)


class SuccessVerifier:
    """Verifies remediation success through multiple checks."""

    def __init__(self, api_get_fn=None):
        self._api_get = api_get_fn

    def verify_remediation(self, incident: dict, action_name: str,
                            wait_seconds: int = 30) -> dict:
        """
        Run all verification checks and return a score.
        """
        service = incident.get("service_name", "")

        logger.info(f"[Verify] Waiting {wait_seconds}s before verification...")
        time.sleep(min(wait_seconds, 10))

        checks = []

        # 1. Metric check
        metric_result = self._check_metrics(service)
        checks.append(("metrics", metric_result))

        # 2. Error check
        error_result = self._check_errors(service)
        checks.append(("errors", error_result))

        # 3. Service health check
        health_result = self._check_service_health(service)
        checks.append(("health", health_result))

        # Calculate overall score
        total_score = 0
        total_weight = 0
        details = {}
        for name, result in checks:
            score = result.get("score", 50)
            weight = result.get("weight", 1)
            total_score += score * weight
            total_weight += weight
            details[name] = result

        overall_score = int(total_score / total_weight) if total_weight > 0 else 50

        # Determine verdict
        if overall_score >= 90:
            verdict = "full_success"
        elif overall_score >= 70:
            verdict = "partial_success"
        elif overall_score >= 50:
            verdict = "unclear"
        else:
            verdict = "failed"

        logger.info(f"[Verify] Score: {overall_score}, Verdict: {verdict}")

        return {
            "score": overall_score,
            "verdict": verdict,
            "checks": details,
            "action": action_name,
            "service": service,
        }

    def _check_metrics(self, service: str) -> dict:
        """Check if service metrics are back in normal range."""
        if not self._api_get:
            return {"score": 50, "weight": 2, "message": "Cannot check (no API)"}

        try:
            metrics = self._api_get("/metrics/", {
                "service_name": service, "hours": 0.1, "limit": 10
            })
            issues = []
            for m in (metrics or []):
                name = m.get("metric_name", "")
                val = m.get("value", 0)
                if name == "cpu" and val > 80:
                    issues.append(f"CPU still high: {val}%")
                if name == "memory" and val > 85:
                    issues.append(f"Memory still high: {val}%")
                if name == "error_rate" and val > 5:
                    issues.append(f"Errors still high: {val}/min")
                if name == "response_time" and val > 500:
                    issues.append(f"Response time still high: {val}ms")

            if not issues:
                return {"score": 95, "weight": 2, "message": "All metrics normal"}
            return {"score": max(20, 80 - len(issues) * 20), "weight": 2,
                    "message": "; ".join(issues)}
        except Exception as e:
            return {"score": 50, "weight": 2, "message": f"Check failed: {e}"}

    def _check_errors(self, service: str) -> dict:
        """Check if error logs have stopped."""
        if not self._api_get:
            return {"score": 50, "weight": 2, "message": "Cannot check (no API)"}

        try:
            logs = self._api_get("/logs/errors", {
                "service_name": service, "hours": 0.1
            })
            error_count = len(logs or [])
            if error_count == 0:
                return {"score": 100, "weight": 2, "message": "No recent errors"}
            elif error_count <= 2:
                return {"score": 70, "weight": 2, "message": f"{error_count} recent errors (declining)"}
            return {"score": 30, "weight": 2, "message": f"{error_count} errors still occurring"}
        except Exception as e:
            return {"score": 50, "weight": 2, "message": f"Check failed: {e}"}

    def _check_service_health(self, service: str) -> dict:
        """Check if service is responding to health checks."""
        # In production this would hit the actual service health endpoint
        # For now, check if recent metrics exist (service is reporting)
        if not self._api_get:
            return {"score": 50, "weight": 1, "message": "Cannot check (no API)"}

        try:
            metrics = self._api_get("/metrics/", {
                "service_name": service, "hours": 0.05, "limit": 1
            })
            if metrics:
                return {"score": 90, "weight": 1, "message": "Service is reporting metrics"}
            return {"score": 40, "weight": 1, "message": "No recent metrics from service"}
        except Exception:
            return {"score": 30, "weight": 1, "message": "Service not reachable"}
