"""
Safe Execution Framework: Validates, executes, and monitors remediation actions.
Creates checkpoints before action, auto-rolls back if metrics worsen.
"""
import time
import logging
from datetime import datetime
from typing import Optional

from .safety_rules import SafetyRules
from .checkpoint import CheckpointManager

logger = logging.getLogger(__name__)


class ExecutionResult:
    def __init__(self, success: bool, action_name: str, message: str = "",
                 impact_score: float = 0, rolled_back: bool = False,
                 duration_seconds: float = 0, checkpoint_id: str = ""):
        self.success = success
        self.action_name = action_name
        self.message = message
        self.impact_score = impact_score
        self.rolled_back = rolled_back
        self.duration_seconds = duration_seconds
        self.checkpoint_id = checkpoint_id
        self.executed_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "success": self.success,
            "action_name": self.action_name,
            "message": self.message,
            "impact_score": self.impact_score,
            "rolled_back": self.rolled_back,
            "duration_seconds": self.duration_seconds,
            "checkpoint_id": self.checkpoint_id,
            "executed_at": self.executed_at,
        }


class SafeExecutionFramework:
    """Safely executes remediation actions with validation, checkpoints, and rollback."""

    def __init__(self, api_get_fn=None, api_post_fn=None, dry_run: bool = False):
        self.safety_rules = SafetyRules()
        self.checkpoint_mgr = CheckpointManager()
        self._api_get = api_get_fn
        self._api_post = api_post_fn
        self.dry_run = dry_run
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3  # circuit breaker

    def execute_action(self, action, context: dict) -> ExecutionResult:
        """
        Execute a remediation action safely.
        1. Pre-validation
        2. Create checkpoint
        3. Execute action
        4. Monitor impact
        5. Auto-rollback if worsened
        """
        action_name = action.name if hasattr(action, 'name') else str(action)
        service = context.get("service_name", "unknown")
        start_time = time.time()

        logger.info(f"[SafeExec] Starting action: {action_name} on {service}")

        # Circuit breaker check
        if self._consecutive_failures >= self._max_consecutive_failures:
            msg = f"Circuit breaker open: {self._consecutive_failures} consecutive failures"
            logger.warning(f"[SafeExec] {msg}")
            return ExecutionResult(False, action_name, msg)

        # Step 1: Pre-validation
        can_exec, reason = self.safety_rules.can_execute(action_name, service)
        if not can_exec:
            logger.warning(f"[SafeExec] Blocked: {reason}")
            return ExecutionResult(False, action_name, f"Safety blocked: {reason}")

        # Check approval requirement
        if self.safety_rules.requires_approval(action_name, service):
            if not context.get("approved", False):
                logger.info(f"[SafeExec] Action requires approval")
                return ExecutionResult(False, action_name, "Requires approval")

        # Dry run mode
        if self.dry_run:
            logger.info(f"[SafeExec] DRY RUN: Would execute {action_name} on {service}")
            return ExecutionResult(True, action_name, "Dry run - no action taken",
                                   duration_seconds=time.time() - start_time)

        # Step 2: Create checkpoint
        checkpoint_id = self.checkpoint_mgr.create_checkpoint(service, context)
        logger.info(f"[SafeExec] Checkpoint created: {checkpoint_id}")

        # Step 3: Collect baseline metrics
        baseline = self._collect_metrics(service)

        # Step 4: Execute action
        try:
            if hasattr(action, 'validate'):
                valid, val_msg = action.validate(context)
                if not valid:
                    return ExecutionResult(False, action_name, f"Validation failed: {val_msg}",
                                           checkpoint_id=checkpoint_id)

            if hasattr(action, 'execute'):
                result = action.execute(context)
            else:
                result = {"success": True, "message": "Action executed"}

            if not result.get("success", False):
                self._consecutive_failures += 1
                self.safety_rules.record_action(action_name, service, success=False)
                return ExecutionResult(False, action_name, result.get("message", "Action failed"),
                                       checkpoint_id=checkpoint_id,
                                       duration_seconds=time.time() - start_time)

        except Exception as e:
            self._consecutive_failures += 1
            logger.error(f"[SafeExec] Execution error: {e}")
            self._attempt_rollback(action, checkpoint_id, service, context)
            return ExecutionResult(False, action_name, f"Execution error: {e}",
                                   rolled_back=True, checkpoint_id=checkpoint_id,
                                   duration_seconds=time.time() - start_time)

        # Step 5: Monitor impact (short check)
        logger.info(f"[SafeExec] Monitoring impact for 30 seconds...")
        time.sleep(5)  # Brief wait for metrics to update
        current = self._collect_metrics(service)
        impact = self._calculate_impact(baseline, current)

        # Step 6: Auto-rollback if metrics worsened significantly
        if impact < -20:
            logger.warning(f"[SafeExec] Impact score {impact} < -20, rolling back!")
            self._attempt_rollback(action, checkpoint_id, service, context)
            self._consecutive_failures += 1
            self.safety_rules.record_action(action_name, service, success=False)
            return ExecutionResult(False, action_name,
                                   f"Auto-rollback triggered (impact: {impact})",
                                   impact_score=impact, rolled_back=True,
                                   checkpoint_id=checkpoint_id,
                                   duration_seconds=time.time() - start_time)

        # Success
        self._consecutive_failures = 0
        self.safety_rules.record_action(action_name, service, success=True)
        duration = time.time() - start_time

        logger.info(f"[SafeExec] Action completed: {action_name} (impact: {impact}, "
                     f"duration: {duration:.1f}s)")

        return ExecutionResult(True, action_name, "Action executed successfully",
                               impact_score=impact, checkpoint_id=checkpoint_id,
                               duration_seconds=duration)

    def _collect_metrics(self, service: str) -> dict:
        """Collect current metrics for a service."""
        if not self._api_get:
            return {}
        try:
            metrics = self._api_get("/metrics/", {
                "service_name": service, "hours": 0.1, "limit": 10
            })
            result = {}
            for m in (metrics or []):
                result[m.get("metric_name", "")] = m.get("value", 0)
            return result
        except Exception:
            return {}

    def _calculate_impact(self, baseline: dict, current: dict) -> float:
        """Calculate impact score from -100 (much worse) to +100 (much better)."""
        if not baseline or not current:
            return 0  # Can't determine, assume neutral

        scores = []
        # Lower is better for: error_rate, response_time, cpu, memory
        for metric in ["error_rate", "response_time", "cpu", "memory"]:
            before = baseline.get(metric)
            after = current.get(metric)
            if before and after and before > 0:
                change_pct = ((before - after) / before) * 100
                scores.append(min(max(change_pct, -100), 100))

        return sum(scores) / len(scores) if scores else 0

    def _attempt_rollback(self, action, checkpoint_id: str, service: str, context: dict):
        """Attempt to rollback an action."""
        logger.info(f"[SafeExec] Attempting rollback for {service}...")
        try:
            if hasattr(action, 'rollback'):
                action.rollback(context)
            self.checkpoint_mgr.restore_checkpoint(checkpoint_id)
            logger.info(f"[SafeExec] Rollback successful")
        except Exception as e:
            logger.error(f"[SafeExec] Rollback failed: {e}")

    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker."""
        self._consecutive_failures = 0
