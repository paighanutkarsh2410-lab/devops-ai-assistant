"""
Approval Client: Requests and waits for human approval of remediation actions.
"""
import time
import logging

logger = logging.getLogger(__name__)


class ApprovalClient:
    """Client for the approval workflow."""

    def __init__(self, api_get_fn, api_post_fn):
        self._get = api_get_fn
        self._post = api_post_fn

    def request_approval(self, action_name: str, action_description: str,
                          risk_level: str, incident_id: str) -> str:
        """Create an approval request. Returns approval_id."""
        try:
            result = self._post("/approvals/", {
                "incident_id": incident_id,
                "action_name": action_name,
                "action_description": action_description,
                "risk_level": risk_level,
            })
            approval_id = result.get("id", "")
            logger.info(f"[Approval] Requested: {approval_id} for {action_name}")
            return approval_id
        except Exception as e:
            logger.error(f"[Approval] Request failed: {e}")
            return ""

    def wait_for_approval(self, approval_id: str, timeout_minutes: int = 5) -> bool:
        """Poll for approval status. Returns True if approved."""
        if not approval_id:
            return False

        max_checks = timeout_minutes * 6  # Check every 10 seconds
        for i in range(max_checks):
            try:
                status = self.check_approval_status(approval_id)
                if status == "approved":
                    logger.info(f"[Approval] {approval_id} approved")
                    return True
                if status in ("rejected", "expired"):
                    logger.info(f"[Approval] {approval_id} {status}")
                    return False
            except Exception:
                pass
            time.sleep(10)

        logger.warning(f"[Approval] {approval_id} timed out")
        return False

    def check_approval_status(self, approval_id: str) -> str:
        """Check the current status of an approval request."""
        try:
            result = self._get(f"/approvals/{approval_id}")
            return result.get("status", "unknown")
        except Exception:
            return "unknown"
