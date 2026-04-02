"""
Increase Resources Action: Increase CPU/memory limits for a service.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)


class IncreaseResourcesAction(RemediationAction):
    name = "increase_resources"
    description = "Increase CPU/memory resource limits for a service"
    risk_level = "MEDIUM"
    estimated_duration_seconds = 120

    def validate(self, context: dict) -> Tuple[bool, str]:
        service = context.get("service_name")
        if not service:
            return False, "No service_name provided"

        resource_type = context.get("resource_type", "memory")
        if resource_type not in ("cpu", "memory"):
            return False, f"Invalid resource_type: {resource_type}"

        increase_pct = context.get("increase_percent", 50)
        if increase_pct > 100:
            return False, "Cannot increase resources by more than 100%"

        return True, "OK"

    def execute(self, context: dict) -> dict:
        service = context.get("service_name", "")
        resource_type = context.get("resource_type", "memory")
        increase_pct = context.get("increase_percent", 50)
        k8s_ctrl = context.get("k8s_controller")

        if k8s_ctrl:
            # For K8s, patch the deployment resource limits
            namespace = context.get("namespace", "default")
            logger.info(f"[IncreaseResources] Would increase {resource_type} by {increase_pct}% "
                        f"for {service} in {namespace}")
            return {"success": True,
                    "message": f"Resource increase requested: {service} {resource_type} +{increase_pct}%"}

        logger.info(f"[IncreaseResources] Would increase {resource_type} by {increase_pct}% for {service}")
        return {"success": True,
                "message": f"Resource increase requested: {service} {resource_type} +{increase_pct}%"}

    def rollback(self, context: dict) -> dict:
        service = context.get("service_name", "")
        return {"success": True, "message": f"Would revert resource limits for {service}"}
