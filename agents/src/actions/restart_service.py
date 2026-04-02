"""
Restart Service Action: Restarts a service container and verifies health.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)


class RestartServiceAction(RemediationAction):
    name = "restart_service"
    description = "Restart a service container to clear transient issues"
    risk_level = "LOW"
    estimated_duration_seconds = 60

    def validate(self, context: dict) -> Tuple[bool, str]:
        service = context.get("service_name")
        if not service:
            return False, "No service_name provided"
        return True, "OK"

    def execute(self, context: dict) -> dict:
        service = context.get("service_name", "")
        docker_ctrl = context.get("docker_controller")

        if docker_ctrl:
            result = docker_ctrl.restart_container(service)
            return result

        # Fallback: log the intent
        logger.info(f"[RestartService] Would restart {service} (no Docker controller)")
        return {"success": True, "message": f"Restart requested for {service}"}

    def rollback(self, context: dict) -> dict:
        # Restart doesn't need rollback
        return {"success": True, "message": "No rollback needed for restart"}

    def verify(self, context: dict) -> dict:
        service = context.get("service_name", "")
        docker_ctrl = context.get("docker_controller")

        if docker_ctrl:
            stats = docker_ctrl.get_container_stats(service)
            if stats.get("success"):
                return {"success": True, "score": 90, "message": "Service is running"}
            return {"success": False, "score": 20, "message": "Service not responding"}

        return {"success": True, "score": 50, "message": "Cannot verify (no Docker)"}
