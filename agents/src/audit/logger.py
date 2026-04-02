"""
Audit Logger: Wrapper for easy action logging from agents.
"""
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs remediation actions to the backend audit system."""

    def __init__(self, api_post_fn):
        self._post = api_post_fn

    def log_action_start(self, incident_id: str, action_name: str,
                          action_type: str = "remediation") -> str:
        """Log the start of an action."""
        try:
            result = self._post("/audit/actions", {
                "incident_id": incident_id,
                "action_name": action_name,
                "action_type": action_type,
                "executed_by": "RemediationAgent",
                "status": "in_progress",
            })
            return result.get("id", "")
        except Exception as e:
            logger.warning(f"[Audit] Failed to log start: {e}")
            return ""

    def log_action_complete(self, incident_id: str, action_name: str,
                             success: bool, duration: float = 0,
                             impact_score: float = 0, rolled_back: bool = False,
                             error_message: str = ""):
        """Log a completed action."""
        status = "success" if success else ("rollback" if rolled_back else "failure")
        try:
            self._post("/audit/actions", {
                "incident_id": incident_id,
                "action_name": action_name,
                "action_type": "remediation",
                "executed_by": "RemediationAgent",
                "status": status,
                "duration_seconds": duration,
                "impact_score": impact_score,
                "rollback_performed": rolled_back,
                "error_message": error_message,
            })
        except Exception as e:
            logger.warning(f"[Audit] Failed to log completion: {e}")

    def log_rollback(self, incident_id: str, action_name: str, reason: str):
        """Log a rollback event."""
        try:
            self._post("/audit/actions", {
                "incident_id": incident_id,
                "action_name": f"{action_name}_rollback",
                "action_type": "rollback",
                "executed_by": "RemediationAgent",
                "status": "rollback",
                "error_message": reason,
                "rollback_performed": True,
            })
        except Exception as e:
            logger.warning(f"[Audit] Failed to log rollback: {e}")
