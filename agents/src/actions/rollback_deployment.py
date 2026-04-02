"""
Rollback Deployment Action: Roll back to a previous deployment version.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)


class RollbackDeploymentAction(RemediationAction):
    name = "rollback_deployment"
    description = "Rollback to the previous deployment version"
    risk_level = "MEDIUM"
    estimated_duration_seconds = 180

    def validate(self, context: dict) -> Tuple[bool, str]:
        service = context.get("service_name")
        if not service:
            return False, "No service_name provided"
        return True, "OK"

    def execute(self, context: dict) -> dict:
        service = context.get("service_name", "")
        k8s_ctrl = context.get("k8s_controller")

        if k8s_ctrl:
            namespace = context.get("namespace", "default")
            return k8s_ctrl.rollback_deployment(service, namespace)

        # Log intent for Docker environments (manual rollback)
        target_version = context.get("target_version", "previous")
        logger.info(f"[RollbackDeploy] Would rollback {service} to {target_version}")
        return {"success": True, "message": f"Rollback requested: {service} -> {target_version}"}

    def rollback(self, context: dict) -> dict:
        # Rolling back a rollback = redeploy the version we rolled back from
        return {"success": True, "message": "Redeploy previous version to undo rollback"}
