"""
Remediation Agent: Automatically fixes infrastructure issues using safe, audited actions.
Pipeline: Load diagnosis -> Select action -> Safety check -> Execute -> Verify -> Update
"""
import sys
import os
import logging
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from base_agent import BaseAgent
from config import BACKEND_URL, REDIS_URL
from safety.execution_framework import SafeExecutionFramework
from safety.safety_rules import SafetyRules
from actions import ACTION_REGISTRY
from integrations.docker_client import DockerController
from integrations.kubernetes_client import KubernetesController

logger = logging.getLogger(__name__)

# Maps diagnosis keywords to action names
DIAGNOSIS_ACTION_MAP = {
    "restart": "restart_service",
    "memory leak": "restart_service",
    "out of memory": "restart_service",
    "oom": "restart_service",
    "cpu spike": "scale_service",
    "high cpu": "scale_service",
    "scale": "scale_service",
    "rollback": "rollback_deployment",
    "deployment": "rollback_deployment",
    "cache": "clear_cache",
    "stale": "clear_cache",
    "rate limit": "adjust_rate_limit",
    "throttl": "adjust_rate_limit",
    "timeout": "adjust_rate_limit",
    "resource": "increase_resources",
    "disk": "increase_resources",
    "process": "kill_process",
    "stuck": "kill_process",
    "zombie": "kill_process",
}


class RemediationAgent(BaseAgent):
    """Agent that automatically remediates infrastructure incidents."""

    def __init__(self, dry_run: bool = False):
        super().__init__("RemediationAgent")
        self.safety_rules = SafetyRules()
        self.execution_framework = SafeExecutionFramework(dry_run=dry_run)
        self._processed_ids = set()
        self._dry_run = dry_run

        # Initialize infrastructure controllers
        self._docker = None
        self._k8s = None
        try:
            dc = DockerController()
            if dc.is_available():
                self._docker = dc
                logger.info("[RemAgent] Docker controller available")
        except Exception:
            pass
        try:
            kc = KubernetesController()
            if kc.is_available():
                self._k8s = kc
                logger.info("[RemAgent] Kubernetes controller available")
        except Exception:
            pass

    def tick(self):
        """Check for incidents needing remediation."""
        try:
            incidents = self.api_get("/incidents/", {"status": "investigating", "limit": 10})
        except Exception as e:
            print(f"  [RemAgent] Failed to fetch incidents: {e}")
            return

        for incident in incidents:
            inc_id = incident.get("id")
            if inc_id and inc_id not in self._processed_ids:
                root_cause = incident.get("root_cause", "")
                if root_cause and root_cause != "Under investigation":
                    print(f"\n  [RemAgent] Remediating: {incident.get('title')}")
                    self.remediate_incident(incident)
                    self._processed_ids.add(inc_id)

        if not incidents:
            print(f"  [RemAgent] No incidents awaiting remediation")

    def remediate_incident(self, incident: dict):
        """Full remediation pipeline for an incident."""
        inc_id = incident.get("id")
        service = incident.get("service_name", "")
        root_cause = incident.get("root_cause", "")
        solution = incident.get("solution", "")

        # Step 1: Select action
        print(f"    Step 1: Selecting remediation action...")
        action_name = self._select_action(root_cause, solution)
        if not action_name:
            print(f"    No suitable action found for: {root_cause[:80]}")
            self._update_status(inc_id, "needs_human", "No automated action available")
            return

        action_class = ACTION_REGISTRY.get(action_name)
        if not action_class:
            print(f"    Action not found in registry: {action_name}")
            return

        action = action_class()
        print(f"    Selected: {action.name} (risk: {action.risk_level})")

        # Step 2: Safety checks
        print(f"    Step 2: Running safety checks...")
        can_exec, reason = self.safety_rules.can_execute(action_name, service)
        if not can_exec:
            print(f"    Blocked by safety: {reason}")
            self._update_status(inc_id, "needs_human", f"Safety blocked: {reason}")
            return

        needs_approval = self.safety_rules.requires_approval(action_name, service)
        if needs_approval:
            print(f"    Action requires approval - requesting...")
            approved = self._request_and_wait_approval(inc_id, action)
            if not approved:
                print(f"    Approval not granted, skipping")
                self._update_status(inc_id, "needs_human", "Approval not granted")
                return

        if not self.safety_rules.is_risk_level_allowed(action_name):
            print(f"    Risk level {action.risk_level} not allowed for auto-execution")
            self._update_status(inc_id, "needs_human",
                                f"Risk level {action.risk_level} requires manual execution")
            return

        # Step 3: Build context and execute
        print(f"    Step 3: Executing action...")
        context = {
            "service_name": service,
            "incident_id": inc_id,
            "root_cause": root_cause,
            "docker_controller": self._docker,
            "k8s_controller": self._k8s,
            "redis_url": REDIS_URL,
            "approved": needs_approval,
            "target_replicas": 2,  # default scale target
        }

        self.execution_framework._api_get = self.api_get
        self.execution_framework._api_post = self.api_post
        result = self.execution_framework.execute_action(action, context)

        # Step 4: Log the action
        print(f"    Step 4: Logging action...")
        self._log_action(inc_id, action, result, service)

        # Step 5: Verify and update
        if result.success:
            print(f"    Step 5: Verifying fix...")
            time.sleep(5)  # Brief wait
            verification = action.verify(context)
            score = verification.get("score", 50)

            if score >= 70:
                print(f"    Remediation successful (score: {score})")
                self._update_status(inc_id, "resolved",
                                    f"Auto-remediated: {action.name} (score: {score})")
            else:
                print(f"    Partial success (score: {score}), needs review")
                self._update_status(inc_id, "needs_human",
                                    f"Remediation partial: {action.name} (score: {score})")
        else:
            print(f"    Action failed: {result.message}")
            if result.rolled_back:
                print(f"    Rollback was performed")
            self._update_status(inc_id, "needs_human", f"Action failed: {result.message}")

        print(f"    Done: success={result.success}, impact={result.impact_score}")

    def _select_action(self, root_cause: str, solution: str) -> str:
        """Match diagnosis to the best remediation action."""
        text = f"{root_cause} {solution}".lower()

        # Check solution for direct action mentions
        for keyword, action in DIAGNOSIS_ACTION_MAP.items():
            if keyword in text:
                return action

        # Default: restart for most issues
        if any(word in text for word in ["error", "crash", "fail", "unresponsive"]):
            return "restart_service"

        return ""

    def _request_and_wait_approval(self, incident_id: str, action) -> bool:
        """Request approval and wait for response."""
        try:
            resp = self.api_post("/approvals/", {
                "incident_id": incident_id,
                "action_name": action.name,
                "action_description": action.description,
                "risk_level": action.risk_level,
            })
            approval_id = resp.get("id")
            if not approval_id:
                return False

            # Poll for approval (max 5 minutes in agent context)
            for _ in range(30):
                time.sleep(10)
                try:
                    status = self.api_get(f"/approvals/{approval_id}")
                    if status.get("status") == "approved":
                        return True
                    if status.get("status") == "rejected":
                        return False
                except Exception:
                    pass
            return False  # Timeout
        except Exception as e:
            logger.warning(f"[RemAgent] Approval request failed: {e}")
            return False

    def _log_action(self, incident_id: str, action, result, service: str):
        """Log the remediation action to the audit system."""
        try:
            self.api_post("/audit/actions", {
                "incident_id": incident_id,
                "action_name": action.name,
                "action_type": "remediation",
                "executed_by": "RemediationAgent",
                "duration_seconds": result.duration_seconds,
                "status": "success" if result.success else ("rollback" if result.rolled_back else "failure"),
                "impact_score": result.impact_score,
                "rollback_performed": result.rolled_back,
                "error_message": result.message if not result.success else "",
            })
        except Exception as e:
            logger.warning(f"[RemAgent] Failed to log action: {e}")

    def _update_status(self, incident_id: str, status: str, message: str):
        """Update incident status."""
        try:
            headers = self._headers()
            requests.patch(
                f"{BACKEND_URL}/incidents/{incident_id}",
                headers=headers,
                json={"status": status, "solution": message},
                timeout=10
            )
        except Exception as e:
            logger.warning(f"[RemAgent] Failed to update incident: {e}")
