"""
Strategy Selector: Matches incident diagnoses to multi-step remediation strategies.
"""
import logging

logger = logging.getLogger(__name__)


class Strategy:
    """A multi-step remediation plan."""
    def __init__(self, name: str, description: str, steps: list):
        self.name = name
        self.description = description
        self.steps = steps  # List of {"action": str, "params": dict, "condition": str}

    def to_dict(self):
        return {"name": self.name, "description": self.description, "steps": self.steps}


# Pre-defined strategies
STRATEGIES = {
    "memory_leak": Strategy(
        name="memory_leak",
        description="Handle memory leak: restart, then profile if recurring",
        steps=[
            {"action": "restart_service", "params": {}, "condition": "always"},
            {"action": "increase_resources", "params": {"resource_type": "memory", "increase_percent": 50},
             "condition": "if_recurring"},
        ]
    ),
    "cpu_spike": Strategy(
        name="cpu_spike",
        description="Handle CPU spike: scale up, or kill stuck process",
        steps=[
            {"action": "scale_service", "params": {"target_replicas": 3}, "condition": "if_sustained"},
            {"action": "kill_process", "params": {}, "condition": "if_single_process"},
            {"action": "restart_service", "params": {}, "condition": "fallback"},
        ]
    ),
    "api_timeout": Strategy(
        name="api_timeout",
        description="Handle API timeouts: check deps, adjust rate limit, scale",
        steps=[
            {"action": "adjust_rate_limit", "params": {"new_rate_limit": 2000, "duration_minutes": 30},
             "condition": "always"},
            {"action": "scale_service", "params": {"target_replicas": 3}, "condition": "if_sustained"},
            {"action": "restart_service", "params": {}, "condition": "fallback"},
        ]
    ),
    "database_slow": Strategy(
        name="database_slow",
        description="Handle slow database: clear cache, restart if needed",
        steps=[
            {"action": "clear_cache", "params": {}, "condition": "always"},
            {"action": "restart_service", "params": {}, "condition": "if_not_improved"},
        ]
    ),
    "disk_full": Strategy(
        name="disk_full",
        description="Handle disk full: clean logs, increase resources",
        steps=[
            {"action": "clear_cache", "params": {"cache_pattern": "tmp:*"}, "condition": "always"},
            {"action": "increase_resources", "params": {"resource_type": "memory", "increase_percent": 50},
             "condition": "if_cloud"},
        ]
    ),
    "deployment_issue": Strategy(
        name="deployment_issue",
        description="Handle bad deployment: immediate rollback",
        steps=[
            {"action": "rollback_deployment", "params": {}, "condition": "always"},
        ]
    ),
}


class StrategySelector:
    """Selects the best remediation strategy based on diagnosis."""

    def select_strategy(self, diagnosis: dict) -> Strategy:
        """Match diagnosis to a strategy."""
        root_cause = (diagnosis.get("root_cause", "") or "").lower()
        severity = (diagnosis.get("severity", "") or "").lower()

        # Pattern matching
        if any(kw in root_cause for kw in ["memory", "leak", "oom", "heap"]):
            return STRATEGIES["memory_leak"]
        if any(kw in root_cause for kw in ["cpu", "spike", "load"]):
            return STRATEGIES["cpu_spike"]
        if any(kw in root_cause for kw in ["timeout", "latency", "slow response"]):
            return STRATEGIES["api_timeout"]
        if any(kw in root_cause for kw in ["database", "query", "sql", "lock"]):
            return STRATEGIES["database_slow"]
        if any(kw in root_cause for kw in ["disk", "storage", "full"]):
            return STRATEGIES["disk_full"]
        if any(kw in root_cause for kw in ["deploy", "rollback", "version", "release"]):
            return STRATEGIES["deployment_issue"]

        # Default: restart
        return Strategy(
            name="generic_restart",
            description="Generic restart strategy",
            steps=[{"action": "restart_service", "params": {}, "condition": "always"}]
        )

    def get_first_action(self, strategy: Strategy) -> dict:
        """Get the first unconditional action from a strategy."""
        for step in strategy.steps:
            if step.get("condition") in ("always", None):
                return step
        return strategy.steps[0] if strategy.steps else {}
