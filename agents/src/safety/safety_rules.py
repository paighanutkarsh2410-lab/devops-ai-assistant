"""
Safety Rules: Enforces safety policies for remediation actions.
Prevents runaway automation and protects critical services.
"""
import os
import yaml
import logging
from datetime import datetime, timedelta
from typing import Tuple

logger = logging.getLogger(__name__)

# Default safety configuration
DEFAULT_CONFIG = {
    "max_restarts_per_hour": 3,
    "auto_remediation_enabled": True,
    "allowed_risk_levels": ["LOW", "MEDIUM"],
    "approval_required_services": ["payment-api", "database-primary"],
    "approval_required_actions": ["kill_process", "rollback_deployment", "increase_resources"],
    "excluded_services": [],
    "blackout_windows": [],
    "max_retries_per_incident": 3,
}


class SafetyRules:
    """Enforces safety rules for remediation actions."""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self._action_history: list = []  # [{action, service, timestamp, success}]

    def _load_config(self, config_path: str = None) -> dict:
        """Load safety config from YAML file or use defaults."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    loaded = yaml.safe_load(f) or {}
                merged = {**DEFAULT_CONFIG, **loaded}
                logger.info(f"[Safety] Loaded config from {config_path}")
                return merged
            except Exception as e:
                logger.warning(f"[Safety] Failed to load config: {e}, using defaults")
        return DEFAULT_CONFIG.copy()

    def can_execute(self, action_name: str, service: str) -> Tuple[bool, str]:
        """Check if an action is allowed to execute."""
        # Auto-remediation disabled
        if not self.config.get("auto_remediation_enabled", True):
            return False, "Auto-remediation is disabled"

        # Service excluded
        if service in self.config.get("excluded_services", []):
            return False, f"Service {service} is excluded from auto-remediation"

        # Blackout window check
        if self._in_blackout_window():
            return False, "Currently in blackout window"

        # Restart limit check
        if "restart" in action_name.lower():
            restart_count = self._count_recent_actions("restart", service, hours=1)
            max_restarts = self.config.get("max_restarts_per_hour", 3)
            if restart_count >= max_restarts:
                return False, f"Max restarts ({max_restarts}/hour) reached for {service}"

        # Max retries per incident
        recent_actions = self._count_recent_actions(action_name, service, hours=2)
        max_retries = self.config.get("max_retries_per_incident", 3)
        if recent_actions >= max_retries:
            return False, f"Max retries ({max_retries}) reached for {action_name} on {service}"

        return True, "OK"

    def requires_approval(self, action_name: str, service: str) -> bool:
        """Check if an action requires human approval."""
        # Service-based approval
        if service in self.config.get("approval_required_services", []):
            return True

        # Action-based approval
        if action_name in self.config.get("approval_required_actions", []):
            return True

        return False

    def get_risk_level(self, action_name: str) -> str:
        """Get the risk level for an action."""
        risk_map = {
            "restart_service": "LOW",
            "clear_cache": "LOW",
            "adjust_rate_limit": "LOW",
            "scale_service": "MEDIUM",
            "rollback_deployment": "MEDIUM",
            "increase_resources": "MEDIUM",
            "kill_process": "HIGH",
        }
        return risk_map.get(action_name, "MEDIUM")

    def is_risk_level_allowed(self, action_name: str) -> bool:
        """Check if the action's risk level is allowed for auto-execution."""
        level = self.get_risk_level(action_name)
        allowed = self.config.get("allowed_risk_levels", ["LOW", "MEDIUM"])
        return level in allowed

    def record_action(self, action_name: str, service: str, success: bool):
        """Record an action execution for rate limiting."""
        self._action_history.append({
            "action": action_name,
            "service": service,
            "timestamp": datetime.utcnow(),
            "success": success,
        })
        # Prune old entries (keep last 24h)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._action_history = [a for a in self._action_history if a["timestamp"] > cutoff]

    def _count_recent_actions(self, action_pattern: str, service: str, hours: float) -> int:
        """Count matching actions within the time window."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return sum(
            1 for a in self._action_history
            if action_pattern.lower() in a["action"].lower()
            and a["service"] == service
            and a["timestamp"] > cutoff
        )

    def _in_blackout_window(self) -> bool:
        """Check if current time is in a blackout window."""
        windows = self.config.get("blackout_windows", [])
        if not windows:
            return False

        now = datetime.utcnow()
        for window in windows:
            try:
                start_h, start_m = map(int, window.get("start", "0:0").split(":"))
                end_h, end_m = map(int, window.get("end", "0:0").split(":"))
                days = window.get("days", [])

                day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                if days and day_names[now.weekday()] not in [d.lower() for d in days]:
                    continue

                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                now_minutes = now.hour * 60 + now.minute

                if start_minutes <= now_minutes <= end_minutes:
                    return True
            except Exception:
                continue

        return False

    def get_rollback_plan(self, action_name: str) -> dict:
        """Get the rollback plan for an action."""
        plans = {
            "restart_service": {"action": "none", "description": "No rollback needed for restart"},
            "scale_service": {"action": "scale_down", "description": "Scale back to original replicas"},
            "rollback_deployment": {"action": "redeploy", "description": "Redeploy the rolled-back version"},
            "clear_cache": {"action": "none", "description": "Cache will rebuild naturally"},
            "kill_process": {"action": "restart_service", "description": "Restart service if process was needed"},
            "increase_resources": {"action": "decrease_resources", "description": "Revert resource limits"},
            "adjust_rate_limit": {"action": "restore_rate_limit", "description": "Restore original rate limit"},
        }
        return plans.get(action_name, {"action": "manual", "description": "Manual rollback required"})
