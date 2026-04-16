"""
Remediation Strategy Engine: Multi-step remediation plans with conditional logic,
retry strategies, parallel execution, gradual rollout, and context-aware decisions.
"""
import time
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    step_id: str
    action: str
    status: StepStatus
    message: str = ""
    duration_ms: float = 0
    output: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyResult:
    strategy_name: str
    status: str = "pending"
    steps_completed: int = 0
    steps_total: int = 0
    step_results: List[StepResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0
    partial: bool = False
    needs_human: bool = False
    human_reason: str = ""


class RemediationStrategyEngine:
    """
    Executes multi-step remediation strategies with branching logic,
    retries, parallel steps, and context-aware behavior.
    """

    def __init__(self):
        self._action_handlers: Dict[str, Callable] = {}
        self._execution_log: List[StrategyResult] = []
        self._lock = threading.Lock()
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register simulated action handlers."""
        actions = [
            "analyze_slow_queries", "kill_slow_queries", "monitor_improvement",
            "restart_database_connection_pool", "escalate_to_human",
            "restart_service", "scale_service", "clear_cache",
            "rollback_deployment", "increase_resources", "run_health_check",
            "flush_dns_cache", "rotate_certificates", "clean_disk_space",
            "optimize_queries", "drain_node", "cordon_node",
            "enable_rate_limiting", "disable_feature_flag",
        ]
        for action in actions:
            self._action_handlers[action] = self._make_simulated_handler(action)

    def _make_simulated_handler(self, action: str) -> Callable:
        def handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            # Simulate execution
            time.sleep(0.01)
            return {"action": action, "status": "success", "message": f"{action} completed"}
        return handler

    def register_action(self, name: str, handler: Callable):
        """Register a custom action handler."""
        self._action_handlers[name] = handler

    # ── Strategy Execution ────────────────────────────────────────────

    def execute_strategy(self, strategy: Dict[str, Any],
                         context: Optional[Dict[str, Any]] = None,
                         dry_run: bool = False) -> StrategyResult:
        """Execute a multi-step remediation strategy."""
        context = context or {}
        steps = strategy.get("steps", [])
        name = strategy.get("name", "unnamed")
        execution_mode = strategy.get("mode", "sequential")

        result = StrategyResult(
            strategy_name=name,
            steps_total=len(steps),
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        start = time.time()

        try:
            if execution_mode == "parallel":
                self._execute_parallel(steps, context, result, dry_run)
            else:
                self._execute_sequential(steps, context, result, dry_run)
        except Exception as e:
            result.status = "error"
            logger.error(f"[StrategyEngine] Strategy '{name}' failed: {e}")

        result.duration_ms = round((time.time() - start) * 1000)
        result.completed_at = datetime.now(timezone.utc).isoformat()

        if result.status == "pending":
            all_success = all(s.status == StepStatus.SUCCESS for s in result.step_results)
            any_failed = any(s.status == StepStatus.FAILED for s in result.step_results)
            result.status = "completed" if all_success else "partial" if any_failed else "completed"
            result.partial = not all_success and result.steps_completed > 0

        with self._lock:
            self._execution_log.append(result)

        return result

    def _execute_sequential(self, steps: List[Dict], context: Dict,
                            result: StrategyResult, dry_run: bool):
        """Execute steps sequentially with branching."""
        step_map = {s.get("order", i + 1): s for i, s in enumerate(steps)}
        current = min(step_map.keys()) if step_map else None

        while current and current in step_map:
            step = step_map[current]
            action = step.get("action", "")
            condition = step.get("condition")

            # Check condition
            if condition and not self._evaluate_condition(condition, context):
                result.step_results.append(StepResult(
                    step_id=f"step_{current}", action=action,
                    status=StepStatus.SKIPPED, message=f"Condition not met: {condition}",
                ))
                current = step.get("on_failure")
                if isinstance(current, str) and current.startswith("step_"):
                    current = int(current.split("_")[1])
                elif current == "complete":
                    break
                continue

            # Execute step
            step_result = self._execute_step(step, context, dry_run)
            result.step_results.append(step_result)

            if step_result.status == StepStatus.SUCCESS:
                result.steps_completed += 1
                next_step = step.get("on_success", "complete")
            else:
                # Retry logic
                retry_config = step.get("retry", {})
                if retry_config and step_result.status == StepStatus.FAILED:
                    retried = self._retry_step(step, context, retry_config, dry_run)
                    if retried.status == StepStatus.SUCCESS:
                        result.step_results.append(retried)
                        result.steps_completed += 1
                        next_step = step.get("on_success", "complete")
                    else:
                        next_step = step.get("on_failure", "complete")
                else:
                    next_step = step.get("on_failure", "complete")

            if next_step == "complete":
                break
            elif isinstance(next_step, str) and next_step.startswith("step_"):
                current = int(next_step.split("_")[1])
            elif isinstance(next_step, int):
                current = next_step
            else:
                break

        # Check if we need human
        if any(s.action == "escalate_to_human" and s.status == StepStatus.SUCCESS
               for s in result.step_results):
            result.needs_human = True
            result.human_reason = "Automated recovery failed — escalating"

    def _execute_parallel(self, steps: List[Dict], context: Dict,
                          result: StrategyResult, dry_run: bool):
        """Execute all steps in parallel."""
        with ThreadPoolExecutor(max_workers=len(steps)) as executor:
            futures = {
                executor.submit(self._execute_step, step, context, dry_run): step
                for step in steps
            }
            for future in as_completed(futures, timeout=120):
                step_result = future.result()
                result.step_results.append(step_result)
                if step_result.status == StepStatus.SUCCESS:
                    result.steps_completed += 1

    def _execute_step(self, step: Dict, context: Dict, dry_run: bool) -> StepResult:
        """Execute a single step."""
        action = step.get("action", "unknown")
        params = step.get("params", {})
        order = step.get("order", 0)

        if dry_run:
            return StepResult(
                step_id=f"step_{order}", action=action,
                status=StepStatus.SUCCESS, message=f"[DRY RUN] Would execute: {action}",
            )

        handler = self._action_handlers.get(action)
        if not handler:
            return StepResult(
                step_id=f"step_{order}", action=action,
                status=StepStatus.FAILED, message=f"No handler for action: {action}",
            )

        start = time.time()
        try:
            output = handler(params, context)
            duration = (time.time() - start) * 1000
            return StepResult(
                step_id=f"step_{order}", action=action,
                status=StepStatus.SUCCESS, message=output.get("message", ""),
                duration_ms=round(duration, 1), output=output,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return StepResult(
                step_id=f"step_{order}", action=action,
                status=StepStatus.FAILED, message=str(e),
                duration_ms=round(duration, 1),
            )

    def _retry_step(self, step: Dict, context: Dict,
                    retry_config: Dict, dry_run: bool) -> StepResult:
        """Retry a step with exponential backoff."""
        max_retries = retry_config.get("max_retries", 3)
        backoff = retry_config.get("backoff_sec", 1.0)

        for attempt in range(max_retries):
            time.sleep(backoff * (2 ** attempt) * 0.01)  # Scaled down for simulation
            result = self._execute_step(step, context, dry_run)
            if result.status == StepStatus.SUCCESS:
                result.message += f" (retry #{attempt + 1})"
                return result

        return StepResult(
            step_id=f"step_{step.get('order', 0)}", action=step.get("action", ""),
            status=StepStatus.FAILED, message=f"Failed after {max_retries} retries",
        )

    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """Evaluate a simple condition string against context."""
        # Simple conditions like "query_time > 30s", "error_rate > 5"
        parts = condition.replace("s", "").split()
        if len(parts) == 3:
            metric, op, value = parts
            current = context.get(metric, 0)
            try:
                threshold = float(value)
                if op == ">":
                    return current > threshold
                elif op == "<":
                    return current < threshold
                elif op == ">=":
                    return current >= threshold
                elif op == "==":
                    return current == threshold
            except ValueError:
                pass
        return True  # Default to true if condition can't be parsed

    # ── Context-Aware ─────────────────────────────────────────────────

    def get_context_strategy(self, issue_type: str,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """Select strategy based on context (time of day, environment, etc.)."""
        context = context or {}
        hour = datetime.now(timezone.utc).hour
        env = context.get("environment", "production")

        if env == "staging":
            return "aggressive"

        # Business hours: gentle, off-hours: aggressive
        if 9 <= hour <= 17:
            return "gentle"
        return "aggressive"

    def estimate_success_probability(self, strategy: Dict[str, Any]) -> float:
        """Estimate success probability based on historical data."""
        steps = strategy.get("steps", [])
        if not steps:
            return 0.0

        # Simulated probability based on step count and known action success rates
        action_rates = {
            "restart_service": 0.88, "scale_service": 0.82, "clear_cache": 0.76,
            "rollback_deployment": 0.72, "escalate_to_human": 1.0,
            "monitor_improvement": 0.90, "analyze_slow_queries": 0.85,
        }

        probabilities = [action_rates.get(s.get("action", ""), 0.75) for s in steps]
        # Overall probability = product of individual steps (simplified)
        overall = 1.0
        for p in probabilities:
            overall *= p
        return round(overall * 100, 1)

    @property
    def execution_history(self) -> List[Dict[str, Any]]:
        return [
            {
                "strategy": r.strategy_name,
                "status": r.status,
                "steps_completed": r.steps_completed,
                "steps_total": r.steps_total,
                "duration_ms": r.duration_ms,
                "partial": r.partial,
                "needs_human": r.needs_human,
                "started_at": r.started_at,
            }
            for r in self._execution_log[-50:]
        ]
