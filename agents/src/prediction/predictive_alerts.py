"""
Predictive Alert Manager: Creates, prioritizes, and tracks
prediction-based alerts. Different from reactive alerts — these
are lower urgency (preventive) and include suggested actions.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Prevention action suggestions per prediction type
PREVENTION_ACTIONS = {
    "resource_exhaustion": [
        {"action": "scale_service", "description": "Add instances before exhaustion", "effort": "low"},
        {"action": "optimize_resources", "description": "Review and optimize resource usage", "effort": "medium"},
        {"action": "increase_resources", "description": "Increase CPU/memory limits", "effort": "low"},
    ],
    "capacity_breach": [
        {"action": "scale_service", "description": "Scale horizontally before breach", "effort": "low"},
        {"action": "plan_migration", "description": "Plan migration to larger instances", "effort": "high"},
    ],
    "degrading_trend": [
        {"action": "investigate", "description": "Investigate root cause of degradation", "effort": "medium"},
        {"action": "restart_service", "description": "Restart to clear accumulated issues", "effort": "low"},
        {"action": "clear_cache", "description": "Clear caches if response time degrading", "effort": "low"},
    ],
    "cost_overrun": [
        {"action": "optimize_resources", "description": "Right-size instances", "effort": "medium"},
        {"action": "review_scaling", "description": "Review auto-scaling policies", "effort": "medium"},
    ],
    "anomaly_forecast": [
        {"action": "monitor_closely", "description": "Increase monitoring frequency", "effort": "low"},
        {"action": "prepare_runbook", "description": "Prepare incident runbook", "effort": "medium"},
    ],
}


class PredictiveAlertManager:
    """Manages predictive alerts with prioritization and prevention tracking."""

    def __init__(self, api_get=None, api_post=None):
        self._api_get = api_get
        self._api_post = api_post
        self._active_alerts = []

    def create_predictive_alert(self, prediction: dict) -> Dict[str, Any]:
        """
        Create a predictive alert from a prediction result.

        Args:
            prediction: Dict with prediction_type, service_name, severity, etc.
        """
        alert = {
            "title": prediction.get("title", "Predicted Issue"),
            "message": prediction.get("message", ""),
            "severity": prediction.get("severity", "low"),
            "prediction_type": prediction.get("prediction_type", "unknown"),
            "service_name": prediction.get("service_name", ""),
            "metric_name": prediction.get("metric_name", ""),
            "confidence": prediction.get("confidence", 50),
            "forecasted_date": prediction.get("forecasted_date"),
            "hours_until_issue": prediction.get("hours_until_breach"),
            "prevented": False,
            "prevention_action": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "preventive_actions": self._suggest_preventive_actions(
                prediction.get("prediction_type", "")
            ),
        }

        self._active_alerts.append(alert)

        # Store via API
        if self._api_post:
            try:
                self._api_post("/alerts/predictive", alert)
            except Exception:
                pass

        return alert

    def prioritize_predictive_alerts(
        self, alerts: List[dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank predictive alerts by priority.

        Score = time_urgency * severity_weight * confidence * (1 - prevention_difficulty)
        """
        if alerts is None:
            alerts = self._active_alerts

        severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.3}

        scored = []
        for alert in alerts:
            if alert.get("prevented"):
                continue

            hours = alert.get("hours_until_issue")
            time_urgency = 1.0
            if hours is not None:
                if hours < 6:
                    time_urgency = 1.0
                elif hours < 24:
                    time_urgency = 0.8
                elif hours < 72:
                    time_urgency = 0.5
                else:
                    time_urgency = 0.3

            severity = severity_weights.get(alert.get("severity", "low"), 0.3)
            confidence = alert.get("confidence", 50) / 100

            score = time_urgency * severity * confidence
            scored.append({**alert, "priority_score": round(score, 3)})

        return sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    def suggest_preventive_actions(
        self, prediction_type: str
    ) -> List[Dict[str, Any]]:
        """Get suggested preventive actions for a prediction type."""
        return self._suggest_preventive_actions(prediction_type)

    def mark_as_prevented(
        self, alert_index: int, action_taken: str = ""
    ) -> bool:
        """Mark a predictive alert as prevented (action was taken)."""
        if 0 <= alert_index < len(self._active_alerts):
            self._active_alerts[alert_index]["prevented"] = True
            self._active_alerts[alert_index]["prevention_action"] = action_taken
            self._active_alerts[alert_index]["prevented_at"] = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_prevention_stats(self) -> Dict[str, Any]:
        """Track how many predictions led to preventive action."""
        total = len(self._active_alerts)
        prevented = sum(1 for a in self._active_alerts if a.get("prevented"))
        expired = sum(
            1 for a in self._active_alerts
            if not a.get("prevented") and self._is_expired(a)
        )

        return {
            "total_predictions": total,
            "prevented": prevented,
            "expired_without_action": expired,
            "prevention_rate": round(prevented / total * 100, 1) if total > 0 else 0,
            "active": total - prevented - expired,
        }

    def _suggest_preventive_actions(self, prediction_type: str) -> List[dict]:
        """Get prevention actions for a prediction type."""
        return PREVENTION_ACTIONS.get(prediction_type, [
            {"action": "investigate", "description": "Review the predicted issue", "effort": "medium"}
        ])

    def _is_expired(self, alert: dict) -> bool:
        """Check if a prediction has passed its forecasted date."""
        fd = alert.get("forecasted_date")
        if not fd:
            return False
        try:
            forecast_dt = datetime.fromisoformat(str(fd).replace("Z", ""))
            return datetime.now(timezone.utc) > forecast_dt
        except (ValueError, TypeError):
            return False
