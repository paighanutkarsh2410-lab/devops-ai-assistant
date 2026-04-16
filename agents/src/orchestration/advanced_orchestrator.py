"""
Advanced Orchestrator: Multi-agent coordination with parallel execution,
conflict resolution, dynamic team creation, and resource management.
"""
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from collections import defaultdict

from .agent_registry import AgentRegistry, AgentEntry, AgentCapability, AgentStatus

logger = logging.getLogger(__name__)


# ── Workflow Patterns ──────────────────────────────────────────────────

class WorkflowPattern(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"


@dataclass
class AgentTask:
    task_id: str
    agent_id: str
    task_type: str  # diagnose, remediate, predict, investigate
    parameters: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # task_ids that must complete first
    priority: int = 5  # 1=highest
    timeout_seconds: int = 120
    status: str = "pending"  # pending, running, completed, failed, cancelled
    result: Any = None
    error: Optional[str] = None
    started_at: float = 0
    completed_at: float = 0


@dataclass
class AgentTeam:
    team_id: str
    incident_id: str
    pattern: WorkflowPattern
    agents: List[str]  # agent_ids
    tasks: List[AgentTask] = field(default_factory=list)
    shared_context: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0
    status: str = "active"


@dataclass
class CoordinationMetrics:
    total_coordinations: int = 0
    avg_time_to_consensus_ms: float = 0
    conflict_count: int = 0
    escalation_count: int = 0
    pattern_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    bottleneck_agents: List[str] = field(default_factory=list)


# ── Incident-to-Domain Mapping ─────────────────────────────────────────

INCIDENT_DOMAIN_MAP = {
    "memory": ["memory", "performance"],
    "leak": ["memory", "performance"],
    "oom": ["memory"],
    "cpu": ["performance", "api"],
    "latency": ["network", "api", "database"],
    "timeout": ["network", "api"],
    "dns": ["network"],
    "connection": ["network", "database"],
    "query": ["database"],
    "deadlock": ["database"],
    "slow query": ["database"],
    "index": ["database"],
    "pool": ["database"],
    "auth": ["api", "security"],
    "rate limit": ["api"],
    "certificate": ["security", "network"],
    "intrusion": ["security"],
    "vulnerability": ["security"],
    "cost": ["cost"],
    "scaling": ["performance", "cost"],
    "disk": ["performance"],
    "error rate": ["api", "performance"],
    "deployment": ["api", "performance"],
    "rollback": ["api"],
}


class AdvancedOrchestrator:
    """Coordinates multi-agent workflows with parallel execution and conflict resolution."""

    def __init__(self, max_workers: int = 8):
        self.registry = AgentRegistry()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._teams: Dict[str, AgentTeam] = {}
        self._task_queue: List[AgentTask] = []
        self._lock = threading.Lock()
        self._metrics = CoordinationMetrics()
        self._message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._shared_stores: Dict[str, Dict] = {}  # per-incident shared context
        self._max_concurrent_teams = 5

        # Register built-in agent types
        self._register_core_agents()

    def _register_core_agents(self):
        """Register the standard agent pipeline."""
        self.registry.register("monitor-agent", "monitor", [
            AgentCapability("monitoring", "Real-time metric monitoring",
                            domains=["monitoring"], actions=["detect", "alert"]),
        ])
        self.registry.register("diagnostic-agent", "diagnostic", [
            AgentCapability("diagnosis", "Root cause analysis",
                            domains=["all"], actions=["diagnose", "correlate"]),
        ])
        self.registry.register("remediation-agent", "remediation", [
            AgentCapability("remediation", "Automated fixes",
                            domains=["all"], actions=["remediate", "rollback"]),
        ])
        self.registry.register("learning-agent", "learning", [
            AgentCapability("learning", "Pattern learning and recommendations",
                            domains=["all"], actions=["learn", "recommend"]),
        ])
        self.registry.register("prediction-agent", "prediction", [
            AgentCapability("prediction", "Forecasting and capacity planning",
                            domains=["all"], actions=["predict", "forecast"]),
        ])

    # ── Multi-Agent Coordination ───────────────────────────────────────

    def coordinate_multi_agent_response(self, incident: dict,
                                         pattern: WorkflowPattern = None) -> dict:
        """Full multi-agent response to an incident."""
        incident_id = incident.get("id", "unknown")
        start_time = time.time()

        # Select workflow pattern based on severity and type
        if pattern is None:
            pattern = self._select_pattern(incident)

        logger.info(f"[Orchestrator] Coordinating {pattern.value} response for {incident_id}")

        # Create agent team
        team = self.create_agent_team(incident, pattern)
        self._teams[team.team_id] = team

        # Initialize shared context
        self._shared_stores[incident_id] = {
            "incident": incident,
            "findings": [],
            "recommendations": [],
            "consensus": None,
        }

        # Execute based on pattern
        if pattern == WorkflowPattern.SEQUENTIAL:
            result = self._execute_sequential(team)
        elif pattern == WorkflowPattern.PARALLEL:
            result = self._execute_parallel(team)
        elif pattern == WorkflowPattern.HIERARCHICAL:
            result = self._execute_hierarchical(team)
        else:
            result = self._execute_sequential(team)

        # Resolve any conflicts
        if len(result.get("agent_results", {})) > 1:
            consensus = self.resolve_conflicts(result.get("agent_results", {}))
            result["consensus"] = consensus

        # Update metrics
        elapsed = (time.time() - start_time) * 1000
        self._metrics.total_coordinations += 1
        n = self._metrics.total_coordinations
        self._metrics.avg_time_to_consensus_ms = (
            self._metrics.avg_time_to_consensus_ms * (n - 1) + elapsed
        ) / n
        self._metrics.pattern_usage[pattern.value] += 1

        team.completed_at = time.time()
        team.status = "completed"

        result["coordination_time_ms"] = round(elapsed, 1)
        result["pattern"] = pattern.value
        result["team_id"] = team.team_id

        return result

    def _select_pattern(self, incident: dict) -> WorkflowPattern:
        """Dynamically select the best workflow pattern."""
        severity = incident.get("severity", "medium")
        root_cause = incident.get("root_cause", "")

        # Critical incidents get parallel investigation
        if severity in ("critical", "high"):
            return WorkflowPattern.PARALLEL

        # Complex multi-domain issues get hierarchical
        domains = self._identify_domains(incident)
        if len(domains) >= 3:
            return WorkflowPattern.HIERARCHICAL

        # Default sequential for standard incidents
        return WorkflowPattern.SEQUENTIAL

    def _identify_domains(self, incident: dict) -> List[str]:
        """Identify which problem domains an incident spans."""
        text = f"{incident.get('title', '')} {incident.get('root_cause', '')} {incident.get('description', '')}".lower()
        domains = set()
        for keyword, domain_list in INCIDENT_DOMAIN_MAP.items():
            if keyword in text:
                domains.update(domain_list)
        return list(domains) if domains else ["general"]

    # ── Team Creation ──────────────────────────────────────────────────

    def create_agent_team(self, incident: dict,
                          pattern: WorkflowPattern = WorkflowPattern.PARALLEL) -> AgentTeam:
        """Analyze incident and assemble the best team of agents."""
        incident_id = incident.get("id", "unknown")
        domains = self._identify_domains(incident)

        # Always include core agents
        team_agents = ["diagnostic-agent", "learning-agent"]

        # Add domain specialists
        for domain in domains:
            specialists = self.registry.find_agents_for_domain(domain)
            for s in specialists[:2]:  # max 2 per domain
                if s.agent_id not in team_agents:
                    team_agents.append(s.agent_id)

        # Add remediation if severity warrants auto-fix
        severity = incident.get("severity", "medium")
        if severity in ("critical", "high"):
            team_agents.append("remediation-agent")
            team_agents.append("prediction-agent")

        team = AgentTeam(
            team_id=f"team-{incident_id}-{int(time.time())}",
            incident_id=incident_id,
            pattern=pattern,
            agents=team_agents,
        )

        # Create tasks for each agent
        for agent_id in team_agents:
            task_type = self._agent_to_task_type(agent_id)
            deps = self._get_task_dependencies(agent_id, pattern, team_agents)
            task = AgentTask(
                task_id=f"{agent_id}-{incident_id}",
                agent_id=agent_id,
                task_type=task_type,
                parameters={"incident": incident, "domains": domains},
                dependencies=deps,
                priority=2 if severity == "critical" else 5,
            )
            team.tasks.append(task)

        logger.info(f"[Orchestrator] Created team {team.team_id} with {len(team_agents)} agents: {team_agents}")
        return team

    def _agent_to_task_type(self, agent_id: str) -> str:
        mapping = {
            "diagnostic-agent": "diagnose",
            "remediation-agent": "remediate",
            "learning-agent": "check_history",
            "prediction-agent": "forecast_impact",
            "monitor-agent": "monitor",
        }
        # Specialists
        if "database" in agent_id:
            return "analyze_database"
        if "network" in agent_id:
            return "diagnose_network"
        if "memory" in agent_id:
            return "analyze_memory"
        if "api" in agent_id:
            return "diagnose_api"
        if "security" in agent_id:
            return "security_audit"
        if "cost" in agent_id:
            return "optimize_costs"
        if "performance" in agent_id:
            return "performance_analysis"
        return mapping.get(agent_id, "investigate")

    def _get_task_dependencies(self, agent_id: str, pattern: WorkflowPattern,
                               team_agents: List[str]) -> List[str]:
        """Determine task dependencies based on workflow pattern."""
        if pattern == WorkflowPattern.PARALLEL:
            return []  # All run in parallel
        if pattern == WorkflowPattern.SEQUENTIAL:
            # Chain: diagnostic → specialists → learning → remediation
            if "remediation" in agent_id:
                return [a for a in team_agents if a != agent_id and "remediation" not in a]
            if "learning" in agent_id:
                return [a for a in team_agents if "diagnostic" in a]
            return []
        # HIERARCHICAL: specialists depend on diagnostic
        if agent_id != "diagnostic-agent" and "diagnostic-agent" in team_agents:
            return ["diagnostic-agent"]
        return []

    # ── Workflow Execution ─────────────────────────────────────────────

    def _execute_sequential(self, team: AgentTeam) -> dict:
        results = {}
        for task in team.tasks:
            task_result = self._run_task(task, team.shared_context)
            results[task.agent_id] = task_result
            team.shared_context.update({task.agent_id: task_result})
        return {"agent_results": results, "status": "completed"}

    def _execute_parallel(self, team: AgentTeam) -> dict:
        results = {}
        completed_tasks = set()

        # Group by dependency level
        def get_ready_tasks():
            return [
                t for t in team.tasks
                if t.task_id not in completed_tasks
                and all(d + "-" in " ".join(completed_tasks) or
                        any(d in ct for ct in completed_tasks)
                        for d in t.dependencies)
            ]

        # Execute in waves
        max_waves = 10
        for wave in range(max_waves):
            ready = get_ready_tasks()
            if not ready:
                break

            futures: Dict[str, Future] = {}
            for task in ready:
                future = self._executor.submit(self._run_task, task, team.shared_context)
                futures[task.task_id] = future

            # Collect results
            for task_id, future in futures.items():
                try:
                    result = future.result(timeout=120)
                    task = next(t for t in team.tasks if t.task_id == task_id)
                    results[task.agent_id] = result
                    team.shared_context[task.agent_id] = result
                    completed_tasks.add(task_id)
                except Exception as e:
                    logger.warning(f"[Orchestrator] Task {task_id} failed: {e}")
                    completed_tasks.add(task_id)
                    results[task_id] = {"error": str(e)}

        return {"agent_results": results, "status": "completed"}

    def _execute_hierarchical(self, team: AgentTeam) -> dict:
        """Hierarchical: coordinator delegates to specialists, aggregates results."""
        # Phase 1: Run diagnostic (coordinator)
        diag_tasks = [t for t in team.tasks if "diagnostic" in t.agent_id]
        diag_results = {}
        for t in diag_tasks:
            diag_results[t.agent_id] = self._run_task(t, team.shared_context)
            team.shared_context[t.agent_id] = diag_results[t.agent_id]

        # Phase 2: Delegate to specialists in parallel
        specialist_tasks = [t for t in team.tasks if t not in diag_tasks]
        futures = {}
        for task in specialist_tasks:
            future = self._executor.submit(self._run_task, task, team.shared_context)
            futures[task.task_id] = future

        specialist_results = {}
        for task_id, future in futures.items():
            try:
                result = future.result(timeout=120)
                task = next(t for t in team.tasks if t.task_id == task_id)
                specialist_results[task.agent_id] = result
            except Exception as e:
                specialist_results[task_id] = {"error": str(e)}

        # Phase 3: Aggregate
        all_results = {**diag_results, **specialist_results}
        aggregated = self._aggregate_results(all_results)

        return {
            "agent_results": all_results,
            "aggregated": aggregated,
            "status": "completed",
        }

    def _run_task(self, task: AgentTask, shared_context: dict) -> dict:
        """Execute a single agent task with tracking."""
        agent = self.registry.get_status(task.agent_id)
        task.status = "running"
        task.started_at = time.time()

        if agent:
            self.registry.acquire_task(task.agent_id)

        try:
            # Simulate agent work (in production, call actual agent methods)
            result = self._dispatch_task(task, shared_context)
            task.status = "completed"
            task.result = result
            elapsed = (time.time() - task.started_at) * 1000

            if agent:
                self.registry.release_task(task.agent_id, success=True,
                                           response_time_ms=elapsed)
            return result

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            elapsed = (time.time() - task.started_at) * 1000

            if agent:
                self.registry.release_task(task.agent_id, success=False,
                                           response_time_ms=elapsed, error=str(e))
            return {"error": str(e), "agent_id": task.agent_id}

        finally:
            task.completed_at = time.time()

    def _dispatch_task(self, task: AgentTask, shared_context: dict) -> dict:
        """Route task to the appropriate agent handler."""
        incident = task.parameters.get("incident", {})
        domains = task.parameters.get("domains", [])

        # Base diagnostic results
        if task.task_type == "diagnose":
            return {
                "agent_id": task.agent_id,
                "task": "diagnosis",
                "root_cause": incident.get("root_cause", "Under investigation"),
                "confidence": 75,
                "domains": domains,
                "evidence": [
                    f"Analyzed metrics for {incident.get('service_name', 'unknown')}",
                    f"Severity: {incident.get('severity', 'unknown')}",
                ],
            }

        if task.task_type == "check_history":
            return {
                "agent_id": task.agent_id,
                "task": "history_check",
                "similar_incidents_found": 3,
                "recommended_action": "restart_service",
                "historical_success_rate": 85,
            }

        if task.task_type == "forecast_impact":
            return {
                "agent_id": task.agent_id,
                "task": "impact_forecast",
                "affected_services": [incident.get("service_name", "unknown")],
                "estimated_impact_duration_min": 30,
                "cascade_risk": "medium",
            }

        if task.task_type == "remediate":
            diag = shared_context.get("diagnostic-agent", {})
            return {
                "agent_id": task.agent_id,
                "task": "remediation",
                "action": "restart_service",
                "based_on": diag.get("root_cause", "unknown"),
                "success_probability": 80,
            }

        # Specialist tasks
        return {
            "agent_id": task.agent_id,
            "task": task.task_type,
            "findings": f"Specialist analysis for {', '.join(domains)}",
            "recommendations": [],
            "confidence": 70,
        }

    def _aggregate_results(self, results: dict) -> dict:
        """Merge results from multiple agents into a unified view."""
        all_evidence = []
        all_recommendations = []
        confidences = []

        for agent_id, result in results.items():
            if isinstance(result, dict) and "error" not in result:
                if "evidence" in result:
                    all_evidence.extend(result["evidence"])
                if "recommendations" in result:
                    all_recommendations.extend(result["recommendations"])
                if "confidence" in result:
                    confidences.append(result["confidence"])
                if "recommended_action" in result:
                    all_recommendations.append(result["recommended_action"])

        return {
            "merged_evidence": all_evidence,
            "all_recommendations": all_recommendations,
            "avg_confidence": round(sum(confidences) / len(confidences), 1) if confidences else 0,
            "agent_count": len(results),
        }

    # ── Conflict Resolution ────────────────────────────────────────────

    def resolve_conflicts(self, agent_results: dict) -> dict:
        """Resolve disagreements between agents using confidence-weighted voting."""
        self._metrics.conflict_count += 1

        diagnoses = {}
        actions = {}

        for agent_id, result in agent_results.items():
            if not isinstance(result, dict) or "error" in result:
                continue

            confidence = result.get("confidence", 50)
            agent_entry = self.registry.get_status(agent_id)
            reliability = agent_entry.success_rate if agent_entry else 80

            # Weight = confidence * historical reliability
            weight = (confidence / 100) * (reliability / 100)

            if "root_cause" in result:
                rc = result["root_cause"]
                diagnoses[rc] = diagnoses.get(rc, 0) + weight

            if "action" in result:
                act = result["action"]
                actions[act] = actions.get(act, 0) + weight
            if "recommended_action" in result:
                act = result["recommended_action"]
                actions[act] = actions.get(act, 0) + weight

        # Pick highest-weighted diagnosis
        best_diagnosis = max(diagnoses, key=diagnoses.get) if diagnoses else "Unknown"
        diag_confidence = round(
            (diagnoses.get(best_diagnosis, 0) / sum(diagnoses.values()) * 100)
            if diagnoses else 0, 1
        )

        # Pick highest-weighted action
        best_action = max(actions, key=actions.get) if actions else None
        action_confidence = round(
            (actions.get(best_action, 0) / sum(actions.values()) * 100)
            if actions and best_action else 0, 1
        )

        # Escalate if low consensus
        needs_escalation = diag_confidence < 50 or (best_action and action_confidence < 50)
        if needs_escalation:
            self._metrics.escalation_count += 1

        return {
            "consensus_diagnosis": best_diagnosis,
            "diagnosis_confidence": diag_confidence,
            "consensus_action": best_action,
            "action_confidence": action_confidence,
            "needs_escalation": needs_escalation,
            "all_diagnoses": dict(diagnoses),
            "all_actions": dict(actions),
            "voting_agents": len(agent_results),
        }

    # ── Inter-Agent Communication ──────────────────────────────────────

    def publish_message(self, channel: str, message: dict):
        """Publish message to agent communication bus."""
        handlers = self._message_handlers.get(channel, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                logger.warning(f"[Orchestrator] Message handler error on {channel}: {e}")

    def subscribe(self, channel: str, handler: Callable):
        self._message_handlers[channel].append(handler)

    def get_shared_context(self, incident_id: str) -> dict:
        return self._shared_stores.get(incident_id, {})

    def update_shared_context(self, incident_id: str, key: str, value: Any):
        if incident_id not in self._shared_stores:
            self._shared_stores[incident_id] = {}
        self._shared_stores[incident_id][key] = value

    # ── Dynamic Agent Spawning ─────────────────────────────────────────

    def spawn_specialist(self, agent_type: str, domain: str,
                         capabilities: List[AgentCapability] = None,
                         ttl_seconds: int = 300) -> AgentEntry:
        """Spawn a temporary specialist agent for a specific task."""
        agent_id = f"temp-{agent_type}-{domain}-{int(time.time())}"
        caps = capabilities or [
            AgentCapability(
                name=f"{domain}_specialist",
                description=f"Temporary {domain} specialist",
                domains=[domain],
                actions=["investigate", "diagnose"],
            )
        ]
        entry = self.registry.register(agent_id, agent_type, caps, max_concurrent=1)
        entry.metadata["temporary"] = True
        entry.metadata["ttl"] = ttl_seconds
        entry.metadata["spawn_time"] = time.time()
        logger.info(f"[Orchestrator] Spawned temporary agent: {agent_id} (TTL={ttl_seconds}s)")

        # Schedule cleanup
        def cleanup():
            time.sleep(ttl_seconds)
            self.registry.unregister(agent_id)
            logger.info(f"[Orchestrator] Cleaned up temporary agent: {agent_id}")

        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

        return entry

    # ── Resource Management ────────────────────────────────────────────

    def get_queue_status(self) -> dict:
        with self._lock:
            return {
                "queued_tasks": len(self._task_queue),
                "active_teams": sum(1 for t in self._teams.values() if t.status == "active"),
                "max_concurrent_teams": self._max_concurrent_teams,
                "registry": self.registry.get_registry_stats(),
            }

    # ── Orchestrator Monitoring ────────────────────────────────────────

    def get_coordination_metrics(self) -> dict:
        return {
            "total_coordinations": self._metrics.total_coordinations,
            "avg_time_to_consensus_ms": round(self._metrics.avg_time_to_consensus_ms, 1),
            "conflict_count": self._metrics.conflict_count,
            "escalation_count": self._metrics.escalation_count,
            "pattern_usage": dict(self._metrics.pattern_usage),
            "active_teams": sum(1 for t in self._teams.values() if t.status == "active"),
            "total_teams": len(self._teams),
            "registry_stats": self.registry.get_registry_stats(),
        }
