"""
Scale Service Action: Scale up or down service replicas.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)


class ScaleServiceAction(RemediationAction):
    name = "scale_service"
    description = "Scale service replicas up or down"
    risk_level = "MEDIUM"
    estimated_duration_seconds = 120

    def validate(self, context: dict) -> Tuple[bool, str]:
        service = context.get("service_name")
        replicas = context.get("target_replicas")
        if not service:
            return False, "No service_name provided"
        if replicas is None or replicas < 1:
            return False, "target_replicas must be >= 1"
        if replicas > 10:
            return False, "Cannot scale beyond 10 replicas without approval"
        return True, "OK"

    def execute(self, context: dict) -> dict:
        service = context.get("service_name", "")
        replicas = context.get("target_replicas", 2)
        docker_ctrl = context.get("docker_controller")
        k8s_ctrl = context.get("k8s_controller")

        if k8s_ctrl:
            namespace = context.get("namespace", "default")
            return k8s_ctrl.scale_deployment(service, replicas, namespace)

        if docker_ctrl:
            return docker_ctrl.scale_service(service, replicas)

        logger.info(f"[ScaleService] Would scale {service} to {replicas} replicas")
        return {"success": True, "message": f"Scale requested: {service} -> {replicas}"}

    def rollback(self, context: dict) -> dict:
        service = context.get("service_name", "")
        original = context.get("original_replicas", 1)
        docker_ctrl = context.get("docker_controller")
        k8s_ctrl = context.get("k8s_controller")

        if k8s_ctrl:
            namespace = context.get("namespace", "default")
            return k8s_ctrl.scale_deployment(service, original, namespace)
        if docker_ctrl:
            return docker_ctrl.scale_service(service, original)

        return {"success": True, "message": f"Would scale {service} back to {original}"}
