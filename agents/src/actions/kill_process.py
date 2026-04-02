"""
Kill Process Action: Kill stuck or zombie processes.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)


class KillProcessAction(RemediationAction):
    name = "kill_process"
    description = "Kill stuck or zombie processes on a service"
    risk_level = "HIGH"
    estimated_duration_seconds = 15

    def validate(self, context: dict) -> Tuple[bool, str]:
        service = context.get("service_name")
        if not service:
            return False, "No service_name provided"

        process_name = context.get("process_name")
        process_pid = context.get("process_pid")
        if not process_name and not process_pid:
            return False, "Provide process_name or process_pid"

        return True, "OK"

    def execute(self, context: dict) -> dict:
        service = context.get("service_name", "")
        process_name = context.get("process_name", "")
        process_pid = context.get("process_pid", "")
        docker_ctrl = context.get("docker_controller")

        target = process_name or f"PID {process_pid}"

        if docker_ctrl:
            # Execute kill inside the container
            try:
                container = docker_ctrl.client.containers.get(service)
                if process_pid:
                    cmd = f"kill -9 {process_pid}"
                else:
                    cmd = f"pkill -9 -f {process_name}"
                exit_code, output = container.exec_run(cmd)
                if exit_code == 0:
                    return {"success": True, "message": f"Killed {target} in {service}"}
                return {"success": False, "message": f"Kill failed (exit {exit_code})"}
            except Exception as e:
                return {"success": False, "message": str(e)}

        logger.info(f"[KillProcess] Would kill {target} on {service}")
        return {"success": True, "message": f"Kill requested: {target} on {service}"}

    def rollback(self, context: dict) -> dict:
        # May need to restart service if killed process was important
        service = context.get("service_name", "")
        return {"success": True, "message": f"Restart {service} if killed process was needed"}
