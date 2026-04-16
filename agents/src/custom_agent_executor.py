"""
Custom Agent Executor: Interprets user-defined agent configurations,
fetches data sources, runs LLM analysis, and executes actions.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CustomAgentExecutor:
    """Executes user-defined custom agents from configuration."""

    TRIGGER_TYPES = {"metric_threshold", "incident_created", "pattern_detected",
                     "schedule", "manual", "webhook"}

    DATA_SOURCES = {"prometheus_metrics", "application_logs", "database_queries",
                    "recent_deployments", "external_api", "cloud_billing"}

    def __init__(self):
        self._execution_log: List[Dict[str, Any]] = []

    def execute_custom_agent(self, agent_config: Dict[str, Any],
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Full execution pipeline for a custom agent.
        1. Evaluate triggers
        2. Fetch data sources
        3. Render and run LLM prompt
        4. Execute actions
        """
        context = context or {}
        start = time.time()
        name = agent_config.get("name", "unnamed")

        result = {
            "agent_name": name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "steps": [],
        }

        try:
            # Step 1: Evaluate triggers
            trigger_result = self._evaluate_triggers(agent_config.get("triggers", {}), context)
            result["steps"].append({"step": "trigger_evaluation", **trigger_result})
            if not trigger_result.get("should_fire"):
                result["status"] = "skipped"
                result["reason"] = "Trigger conditions not met"
                return result

            # Step 2: Fetch data sources
            data = self._fetch_data_sources(agent_config.get("data_sources", []), context)
            result["steps"].append({"step": "data_fetch", "sources": len(data), "status": "complete"})

            # Step 3: Run LLM analysis
            prompt = agent_config.get("analysis_prompt", "")
            analysis = self._run_analysis(prompt, data, context)
            result["steps"].append({"step": "analysis", **analysis})

            # Step 4: Execute actions
            actions = agent_config.get("actions", [])
            action_results = self._execute_actions(actions, analysis, context)
            result["steps"].append({"step": "actions", "results": action_results})

            result["status"] = "completed"
            result["duration_ms"] = round((time.time() - start) * 1000)

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"[CustomAgent] Execution failed for {name}: {e}")

        self._execution_log.append(result)
        return result

    def _evaluate_triggers(self, triggers: Dict[str, Any],
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether trigger conditions are met."""
        if not triggers:
            return {"should_fire": True, "reason": "No triggers (manual)"}

        trigger_type = triggers.get("event") or "metric_threshold"

        if trigger_type == "manual":
            return {"should_fire": True, "reason": "Manual trigger"}

        metric = triggers.get("metric", "")
        threshold = triggers.get("threshold", 0)
        current_value = context.get("metric_value", threshold + 1)

        fired = current_value > threshold
        return {
            "should_fire": fired,
            "trigger_type": trigger_type,
            "metric": metric,
            "threshold": threshold,
            "current_value": current_value,
            "reason": f"{metric}={current_value} {'>' if fired else '<='} {threshold}",
        }

    def _fetch_data_sources(self, sources: List[str],
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from configured sources."""
        data: Dict[str, Any] = {}

        for source in sources:
            if source == "prometheus_metrics":
                data["metrics"] = context.get("metrics", {
                    "cpu_percent": 72.5, "memory_percent": 85.3,
                    "request_rate": 1250, "error_rate": 2.1,
                    "response_time_p95": 450,
                })
            elif source == "application_logs":
                data["logs"] = context.get("logs", [
                    {"level": "ERROR", "message": "Connection pool exhausted", "count": 15},
                    {"level": "WARN", "message": "Slow query detected (>1s)", "count": 42},
                ])
            elif source == "database_queries":
                data["queries"] = context.get("queries", [
                    {"query": "SELECT * FROM orders WHERE ...", "avg_time_ms": 1250, "calls": 500},
                ])
            elif source == "recent_deployments":
                data["deployments"] = context.get("deployments", [
                    {"service": "api-service", "version": "v2.3.1", "deployed_at": "2024-01-15T10:00:00Z"},
                ])
            elif source == "cloud_billing":
                data["billing"] = context.get("billing", {
                    "current_hour": 12.50, "previous_hour": 8.20, "change_pct": 52.4,
                })
            else:
                data[source] = context.get(source, {"status": "no data available"})

        return data

    def _run_analysis(self, prompt_template: str, data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Render prompt template and run LLM analysis (simulated)."""
        # Render template variables
        rendered = prompt_template
        for key, value in {**context, **data}.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))

        # Simulated LLM analysis
        return {
            "prompt_rendered": rendered[:500],
            "analysis": "Based on the data, high memory usage is correlated with increased database connection pool exhaustion. The slow queries are causing connection hold times to increase, leading to memory pressure from queued requests.",
            "confidence": 82,
            "recommendations": [
                "Optimize the top slow queries identified in logs",
                "Increase connection pool size temporarily",
                "Add query result caching for frequently accessed data",
            ],
            "root_cause": "Database slow queries causing connection pool exhaustion",
        }

    def _execute_actions(self, actions: List[Dict[str, Any]],
                         analysis: Dict[str, Any],
                         context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute configured actions."""
        results = []
        for action in actions:
            action_type = action.get("type", "unknown")
            params = action.get("params", {})

            # Simulated action execution
            result = {
                "type": action_type,
                "params": params,
                "status": "executed",
                "message": f"Action '{action_type}' executed successfully",
            }

            if action_type == "notify_slack":
                result["message"] = f"Slack notification sent to {params.get('channel', '#general')}"
            elif action_type == "restart_service":
                result["message"] = f"Service restart initiated for {params.get('service', 'unknown')}"
            elif action_type == "scale_service":
                result["message"] = f"Scaled to {params.get('replicas', 2)} replicas"
            elif action_type == "create_ticket":
                result["message"] = f"Ticket created with priority {params.get('priority', 'medium')}"
                result["ticket_id"] = "TICKET-1234"

            results.append(result)

        return results

    @property
    def execution_history(self) -> List[Dict[str, Any]]:
        return list(self._execution_log[-50:])
