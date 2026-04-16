"""Runbook executor — run automated + manual steps for incident response."""
from sqlalchemy.orm import Session
from datetime import datetime
from models.runbook import Runbook, RunbookExecution
from models.incident import Incident
import logging

logger = logging.getLogger(__name__)


class RunbookExecutor:
    """Executes runbooks step by step, handling automated and manual steps."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def execute_runbook(self, runbook_id: str, incident_id: str = None) -> dict:
        """Execute a runbook against an optional incident."""
        runbook = self.db.query(Runbook).filter(
            Runbook.id == runbook_id, Runbook.user_id == self.user_id
        ).first()
        if not runbook:
            return {"error": "Runbook not found"}

        execution = RunbookExecution(
            runbook_id=runbook.id,
            incident_id=incident_id,
            user_id=self.user_id,
            status="running",
            current_step=0,
            step_results=[],
        )
        self.db.add(execution)
        self.db.commit()

        steps = runbook.steps or []
        step_results = []

        for idx, step in enumerate(steps):
            step_type = step.get("type", "manual")
            result = {
                "order": step.get("order", idx + 1),
                "name": step.get("name", f"Step {idx + 1}"),
                "type": step_type,
                "started_at": datetime.utcnow().isoformat(),
            }

            if step_type == "automated":
                action_result = self._execute_automated(step, incident_id)
                result.update(action_result)
            elif step_type == "manual":
                result["status"] = "pending_manual"
                result["instruction"] = step.get("instruction", "")
                result["assignee_role"] = step.get("assignee_role", "")
            elif step_type == "approval":
                result["status"] = "pending_approval"
                result["approver"] = step.get("approver", "admin")
            elif step_type == "conditional":
                condition = step.get("condition", "")
                result["status"] = "completed"
                result["success"] = True
                result["condition_result"] = True  # simplified

            result["completed_at"] = datetime.utcnow().isoformat()
            step_results.append(result)

            # Stop on automated failure unless configured to continue
            if step_type == "automated" and not result.get("success", True):
                if step.get("on_failure", "stop") == "stop":
                    break

        # Determine status
        has_pending = any(r.get("status") in ("pending_manual", "pending_approval") for r in step_results)
        has_failed = any(r.get("success") is False for r in step_results)

        if has_pending:
            status = "paused"
        elif has_failed:
            status = "failed"
        else:
            status = "completed"

        now = datetime.utcnow()
        execution.status = status
        execution.current_step = len(step_results)
        execution.step_results = step_results
        if status in ("completed", "failed"):
            execution.completed_at = now
            execution.duration_seconds = int((now - execution.started_at).total_seconds())
        self.db.commit()

        return self._serialize_execution(execution)

    def suggest_runbook(self, incident_id: str) -> dict:
        """Suggest a runbook based on incident characteristics."""
        incident = self.db.query(Incident).filter(
            Incident.id == incident_id, Incident.user_id == self.user_id
        ).first()
        if not incident:
            return {"suggestions": []}

        runbooks = self.db.query(Runbook).filter(Runbook.user_id == self.user_id).all()
        suggestions = []

        for rb in runbooks:
            score = 0
            # Match by service
            if rb.service_name and incident.service_name and rb.service_name.lower() == incident.service_name.lower():
                score += 3
            # Match by severity
            if rb.severity and incident.severity and rb.severity == incident.severity:
                score += 1
            # Match by pattern keyword
            if rb.incident_pattern:
                text = f"{incident.title} {incident.description} {incident.root_cause}".lower()
                if rb.incident_pattern.lower() in text:
                    score += 5
            # Match by tags
            for tag in (rb.tags or []):
                text = f"{incident.title} {incident.description}".lower()
                if tag.lower() in text:
                    score += 2

            if score > 0:
                suggestions.append({
                    "runbook_id": str(rb.id),
                    "name": rb.name,
                    "description": rb.description,
                    "match_score": score,
                    "steps_count": len(rb.steps or []),
                    "estimated_duration": rb.estimated_duration_minutes,
                })

        suggestions.sort(key=lambda s: s["match_score"], reverse=True)
        return {"suggestions": suggestions[:5]}

    def get_executions(self, runbook_id: str, limit: int = 20) -> list[dict]:
        execs = (
            self.db.query(RunbookExecution)
            .filter(RunbookExecution.runbook_id == runbook_id, RunbookExecution.user_id == self.user_id)
            .order_by(RunbookExecution.started_at.desc())
            .limit(limit)
            .all()
        )
        return [self._serialize_execution(e) for e in execs]

    def get_analytics(self) -> dict:
        """Runbook usage analytics."""
        execs = self.db.query(RunbookExecution).filter(
            RunbookExecution.user_id == self.user_id
        ).all()

        total = len(execs)
        completed = sum(1 for e in execs if e.status == "completed")
        failed = sum(1 for e in execs if e.status == "failed")
        durations = [e.duration_seconds for e in execs if e.duration_seconds]

        # Most used runbooks
        usage: dict[str, int] = {}
        for e in execs:
            rid = str(e.runbook_id)
            usage[rid] = usage.get(rid, 0) + 1

        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / max(total, 1) * 100, 1),
            "avg_duration_seconds": round(sum(durations) / len(durations)) if durations else 0,
            "most_used": sorted(usage.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def _execute_automated(self, step: dict, incident_id: str = None) -> dict:
        action = step.get("action", "")
        params = step.get("params", {})

        # Simulate automated actions
        actions = {
            "collect_logs": "Collected logs",
            "restart_service": "Service restarted",
            "scale_up": "Scaled up service",
            "clear_cache": "Cache cleared",
            "check_metrics": "Metrics checked",
            "run_health_check": "Health check passed",
            "rollback_deployment": "Deployment rolled back",
            "rotate_credentials": "Credentials rotated",
            "check_disk_space": "Disk space checked",
            "analyze_connections": "Connection pool analyzed",
        }

        message = actions.get(action, f"Executed: {action}")
        return {
            "success": True,
            "status": "completed",
            "action": action,
            "params": params,
            "message": message,
        }

    def _serialize_execution(self, e: RunbookExecution) -> dict:
        return {
            "id": str(e.id),
            "runbook_id": str(e.runbook_id),
            "incident_id": str(e.incident_id) if e.incident_id else None,
            "status": e.status,
            "current_step": e.current_step,
            "step_results": e.step_results,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "duration_seconds": e.duration_seconds,
        }
