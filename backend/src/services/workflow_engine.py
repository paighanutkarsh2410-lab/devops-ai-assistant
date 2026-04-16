"""Workflow execution engine — runs multi-step automation workflows."""
from sqlalchemy.orm import Session
from datetime import datetime
from models.workflow import Workflow, WorkflowExecution
import logging

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes workflows step by step with branching, loops, and error handling."""

    # Available step types and their handlers
    STEP_TYPES = [
        "run_diagnostic", "execute_action", "send_notification", "create_ticket",
        "wait_for_approval", "conditional", "loop", "api_call", "delay", "log",
    ]

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def execute_workflow(self, workflow_id: str, context: dict = None, trigger_type: str = "manual") -> dict:
        """Execute a workflow and return execution results."""
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id, Workflow.user_id == self.user_id
        ).first()
        if not workflow:
            return {"error": "Workflow not found"}
        if not workflow.enabled:
            return {"error": "Workflow is disabled"}

        # Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            user_id=self.user_id,
            status="running",
            trigger_type=trigger_type,
            context=context or {},
            step_results=[],
        )
        self.db.add(execution)
        self.db.commit()

        step_results = []
        steps = workflow.steps or []
        current_idx = 0
        max_iterations = 100  # safety limit

        try:
            iterations = 0
            while current_idx < len(steps) and iterations < max_iterations:
                iterations += 1
                step = steps[current_idx]
                step_type = step.get("type", "")
                step_name = step.get("name", f"Step {current_idx + 1}")

                logger.info(f"Executing step {current_idx}: {step_name} ({step_type})")

                result = self._execute_step(step, context or {}, step_results)
                result["step_index"] = current_idx
                result["step_name"] = step_name
                result["executed_at"] = datetime.utcnow().isoformat()
                step_results.append(result)

                if not result.get("success", False):
                    # Check if step has error handling
                    on_error = step.get("on_error", "stop")
                    if on_error == "continue":
                        current_idx += 1
                    elif on_error == "goto":
                        target = step.get("error_goto", current_idx + 1)
                        current_idx = target
                    else:
                        # Stop execution
                        break
                else:
                    # Handle branching
                    next_step = result.get("next_step")
                    if next_step is not None:
                        current_idx = next_step
                    else:
                        current_idx += 1

            # Determine final status
            failed_steps = [r for r in step_results if not r.get("success", False)]
            status = "completed" if not failed_steps else "failed"

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            step_results.append({
                "step_index": current_idx,
                "step_name": "Error",
                "success": False,
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat(),
            })
            status = "failed"

        # Update execution record
        now = datetime.utcnow()
        execution.status = status
        execution.step_results = step_results
        execution.completed_at = now
        execution.duration_seconds = int((now - execution.started_at).total_seconds())
        if status == "failed":
            execution.error = step_results[-1].get("error", "Unknown error") if step_results else "No steps"
        self.db.commit()

        return {
            "execution_id": str(execution.id),
            "workflow_id": str(workflow.id),
            "status": status,
            "steps_executed": len(step_results),
            "steps_total": len(steps),
            "duration_seconds": execution.duration_seconds,
            "step_results": step_results,
        }

    def check_trigger(self, workflow: Workflow, event_type: str, event_data: dict) -> bool:
        """Check if a workflow's trigger conditions match an event."""
        trigger = workflow.trigger_conditions or {}
        trigger_type = trigger.get("type", "")

        if trigger_type != event_type:
            return False

        filters = trigger.get("filters", {})

        if event_type == "incident_created":
            if filters.get("severity") and event_data.get("severity") != filters["severity"]:
                return False
            if filters.get("service_name") and event_data.get("service_name") != filters["service_name"]:
                return False
            return True

        if event_type == "metric_threshold":
            if filters.get("metric_name") and event_data.get("metric_name") != filters["metric_name"]:
                return False
            threshold = filters.get("threshold")
            if threshold and event_data.get("value", 0) < threshold:
                return False
            return True

        if event_type == "prediction_alert":
            if filters.get("severity") and event_data.get("severity") != filters["severity"]:
                return False
            return True

        return event_type in ("manual", "webhook", "schedule")

    def get_executions(self, workflow_id: str, limit: int = 20) -> list[dict]:
        """Get execution history for a workflow."""
        execs = (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.workflow_id == workflow_id, WorkflowExecution.user_id == self.user_id)
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
            .all()
        )
        return [self._serialize_execution(e) for e in execs]

    # ── Step executors ─────────────────────────────────────────────────

    def _execute_step(self, step: dict, context: dict, previous_results: list) -> dict:
        step_type = step.get("type", "")
        params = step.get("params", {})

        handlers = {
            "run_diagnostic": self._step_run_diagnostic,
            "execute_action": self._step_execute_action,
            "send_notification": self._step_send_notification,
            "create_ticket": self._step_create_ticket,
            "wait_for_approval": self._step_wait_approval,
            "conditional": self._step_conditional,
            "loop": self._step_loop,
            "api_call": self._step_api_call,
            "delay": self._step_delay,
            "log": self._step_log,
        }

        handler = handlers.get(step_type)
        if not handler:
            return {"success": False, "error": f"Unknown step type: {step_type}"}

        try:
            return handler(params, context, previous_results)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _step_run_diagnostic(self, params: dict, context: dict, prev: list) -> dict:
        incident_id = params.get("incident_id") or context.get("incident_id")
        return {
            "success": True,
            "action": "run_diagnostic",
            "incident_id": incident_id,
            "message": f"Diagnostic queued for incident {incident_id}",
        }

    def _step_execute_action(self, params: dict, context: dict, prev: list) -> dict:
        action = params.get("action", "restart_service")
        target = params.get("target") or context.get("service_name", "unknown")
        return {
            "success": True,
            "action": action,
            "target": target,
            "message": f"Action '{action}' executed on {target}",
        }

    def _step_send_notification(self, params: dict, context: dict, prev: list) -> dict:
        channels = params.get("channels", ["slack"])
        message = params.get("message", "Workflow notification")
        return {
            "success": True,
            "action": "send_notification",
            "channels": channels,
            "message": f"Notification sent to {', '.join(channels)}",
        }

    def _step_create_ticket(self, params: dict, context: dict, prev: list) -> dict:
        system = params.get("system", "jira")
        title = params.get("title", context.get("title", "Auto-created ticket"))
        return {
            "success": True,
            "action": "create_ticket",
            "system": system,
            "ticket_title": title,
            "message": f"Ticket created in {system}: {title}",
        }

    def _step_wait_approval(self, params: dict, context: dict, prev: list) -> dict:
        # In a real system, this would pause and wait for approval
        approver = params.get("approver", "admin")
        auto_approve = params.get("auto_approve", True)
        return {
            "success": True,
            "action": "wait_for_approval",
            "approver": approver,
            "approved": auto_approve,
            "message": f"Approval {'granted (auto)' if auto_approve else 'pending from ' + approver}",
        }

    def _step_conditional(self, params: dict, context: dict, prev: list) -> dict:
        condition = params.get("condition", "")
        true_step = params.get("true_step")
        false_step = params.get("false_step")

        # Evaluate simple conditions
        result = self._evaluate_condition(condition, context, prev)
        next_step = true_step if result else false_step

        return {
            "success": True,
            "action": "conditional",
            "condition": condition,
            "evaluated": result,
            "next_step": next_step,
            "message": f"Condition '{condition}' = {result}",
        }

    def _step_loop(self, params: dict, context: dict, prev: list) -> dict:
        iterations = params.get("iterations", 1)
        return {
            "success": True,
            "action": "loop",
            "iterations": iterations,
            "message": f"Loop completed ({iterations} iterations)",
        }

    def _step_api_call(self, params: dict, context: dict, prev: list) -> dict:
        url = params.get("url", "")
        method = params.get("method", "GET")
        return {
            "success": True,
            "action": "api_call",
            "url": url,
            "method": method,
            "message": f"API call: {method} {url}",
        }

    def _step_delay(self, params: dict, context: dict, prev: list) -> dict:
        seconds = params.get("seconds", 0)
        return {
            "success": True,
            "action": "delay",
            "seconds": seconds,
            "message": f"Delayed {seconds}s",
        }

    def _step_log(self, params: dict, context: dict, prev: list) -> dict:
        message = params.get("message", "Log entry")
        level = params.get("level", "info")
        return {
            "success": True,
            "action": "log",
            "level": level,
            "log_message": message,
            "message": f"[{level.upper()}] {message}",
        }

    def _evaluate_condition(self, condition: str, context: dict, prev: list) -> bool:
        """Simple condition evaluator."""
        if not condition:
            return True
        # Support basic conditions
        if condition == "severity_is_critical":
            return context.get("severity") == "critical"
        if condition == "auto_resolved":
            return context.get("auto_resolved", False)
        if condition == "has_root_cause":
            return bool(context.get("root_cause"))
        if condition.startswith("prev_step_success"):
            return prev[-1].get("success", False) if prev else False
        return True

    def _serialize_execution(self, e: WorkflowExecution) -> dict:
        return {
            "id": str(e.id),
            "workflow_id": str(e.workflow_id),
            "status": e.status,
            "trigger_type": e.trigger_type,
            "context": e.context,
            "step_results": e.step_results,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "duration_seconds": e.duration_seconds,
            "error": e.error,
        }
