"""
Agent Health Monitor: Tracks agent health, performance, resource usage, and SLAs.
Provides alerting on failures, stuck agents, and performance degradation.
"""
import time
import logging
import threading
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AgentHealthState:
    agent_name: str
    status: str = "unknown"  # healthy, degraded, unhealthy, stopped
    last_heartbeat: Optional[str] = None
    current_task: Optional[str] = None
    queue_depth: int = 0
    error_count: int = 0
    total_tasks: int = 0
    success_rate: float = 100.0
    avg_task_duration_ms: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_sec: float = 0.0
    started_at: Optional[str] = None


@dataclass
class AgentAlert:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    agent_name: str = ""
    alert_type: str = ""  # crashed, stuck, high_error_rate, slow, queue_backlog
    severity: str = "warning"
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved: bool = False


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    agent_name: str = ""
    operation: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    parent_span: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    status: str = "ok"


class AgentHealthMonitor:
    """
    Monitors all agents for health, performance, and SLA compliance.
    """

    def __init__(self, heartbeat_timeout_sec: float = 60.0):
        self._agents: Dict[str, AgentHealthState] = {}
        self._alerts: List[AgentAlert] = []
        self._traces: Dict[str, List[TraceSpan]] = defaultdict(list)
        self._logs: deque = deque(maxlen=5000)
        self._resource_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._sla_targets: Dict[str, Dict[str, float]] = {}
        self._heartbeat_timeout = heartbeat_timeout_sec
        self._lock = threading.Lock()

        self._init_agents()

    def _init_agents(self):
        """Initialize known agents."""
        agents = [
            ("monitor-agent", 95.2, 22.0, 500),
            ("diagnostic-agent", 88.5, 85.0, 150),
            ("remediation-agent", 82.1, 180.0, 95),
            ("learning-agent", 91.0, 6.5, 200),
            ("prediction-agent", 79.3, 45.0, 80),
        ]
        for name, success_rate, avg_ms, total in agents:
            self._agents[name] = AgentHealthState(
                agent_name=name, status="healthy",
                last_heartbeat=datetime.now(timezone.utc).isoformat(),
                success_rate=success_rate,
                avg_task_duration_ms=avg_ms * 1000,
                total_tasks=total,
                cpu_percent=15 + hash(name) % 30,
                memory_mb=50 + hash(name) % 150,
                uptime_sec=86400 + hash(name) % 86400,
                started_at=(datetime.now(timezone.utc) - timedelta(hours=24 + hash(name) % 48)).isoformat(),
            )

        self._sla_targets = {
            "monitor-agent": {"response_time_ms": 30000, "accuracy_pct": 90, "uptime_pct": 99.5},
            "diagnostic-agent": {"response_time_ms": 120000, "accuracy_pct": 85, "uptime_pct": 99.0},
            "remediation-agent": {"response_time_ms": 300000, "accuracy_pct": 80, "uptime_pct": 99.0},
            "learning-agent": {"response_time_ms": 10000, "accuracy_pct": 85, "uptime_pct": 99.0},
            "prediction-agent": {"response_time_ms": 60000, "accuracy_pct": 75, "uptime_pct": 99.0},
        }

    # ── Heartbeats ────────────────────────────────────────────────────

    def heartbeat(self, agent_name: str, task: Optional[str] = None,
                  queue_depth: int = 0, cpu: float = 0, memory_mb: float = 0):
        """Record a heartbeat from an agent."""
        with self._lock:
            state = self._agents.get(agent_name)
            if not state:
                state = AgentHealthState(agent_name=agent_name)
                self._agents[agent_name] = state

            state.last_heartbeat = datetime.now(timezone.utc).isoformat()
            state.current_task = task
            state.queue_depth = queue_depth
            state.cpu_percent = cpu
            state.memory_mb = memory_mb

            if state.status in ("unhealthy", "stopped"):
                state.status = "healthy"

            self._resource_history[agent_name].append({
                "timestamp": state.last_heartbeat,
                "cpu": cpu, "memory_mb": memory_mb, "queue_depth": queue_depth,
            })

    def record_task(self, agent_name: str, success: bool, duration_ms: float):
        """Record a completed task."""
        with self._lock:
            state = self._agents.get(agent_name)
            if not state:
                return
            state.total_tasks += 1
            if not success:
                state.error_count += 1
            state.success_rate = round(
                (state.total_tasks - state.error_count) / max(state.total_tasks, 1) * 100, 1
            )
            # Running average
            state.avg_task_duration_ms = round(
                (state.avg_task_duration_ms * (state.total_tasks - 1) + duration_ms)
                / state.total_tasks, 1
            )

    # ── Health Checks ─────────────────────────────────────────────────

    def check_health(self) -> List[AgentAlert]:
        """Run health checks on all agents and generate alerts."""
        new_alerts = []
        now = datetime.now(timezone.utc)

        for name, state in self._agents.items():
            # Check heartbeat
            if state.last_heartbeat:
                last = datetime.fromisoformat(state.last_heartbeat)
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                gap = (now - last).total_seconds()
                if gap > self._heartbeat_timeout * 3:
                    state.status = "unhealthy"
                    new_alerts.append(self._alert(name, "crashed", "critical",
                                                  f"No heartbeat for {int(gap)}s"))
                elif gap > self._heartbeat_timeout:
                    state.status = "degraded"
                    new_alerts.append(self._alert(name, "stuck", "warning",
                                                  f"Heartbeat delayed by {int(gap)}s"))

            # Check error rate
            if state.total_tasks > 10 and state.success_rate < 70:
                new_alerts.append(self._alert(name, "high_error_rate", "critical",
                                              f"Success rate dropped to {state.success_rate}%"))
            elif state.total_tasks > 10 and state.success_rate < 85:
                new_alerts.append(self._alert(name, "high_error_rate", "warning",
                                              f"Success rate at {state.success_rate}%"))

            # Check queue backlog
            if state.queue_depth > 50:
                new_alerts.append(self._alert(name, "queue_backlog", "warning",
                                              f"Queue depth: {state.queue_depth}"))

            # Check SLA
            sla = self._sla_targets.get(name, {})
            if sla:
                if state.avg_task_duration_ms > sla.get("response_time_ms", float('inf')):
                    new_alerts.append(self._alert(name, "slow", "warning",
                                                  f"Avg duration {state.avg_task_duration_ms}ms exceeds SLA"))

        self._alerts.extend(new_alerts)
        return new_alerts

    def _alert(self, agent: str, alert_type: str, severity: str, message: str) -> AgentAlert:
        return AgentAlert(agent_name=agent, alert_type=alert_type,
                          severity=severity, message=message)

    # ── Logging ───────────────────────────────────────────────────────

    def log(self, agent_name: str, level: str, message: str,
            correlation_id: Optional[str] = None):
        """Add a structured log entry."""
        self._logs.append({
            "agent": agent_name, "level": level, "message": message,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_logs(self, agent_name: Optional[str] = None, level: Optional[str] = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
        logs = list(self._logs)
        if agent_name:
            logs = [l for l in logs if l["agent"] == agent_name]
        if level:
            logs = [l for l in logs if l["level"] == level]
        return logs[-limit:]

    # ── Tracing ───────────────────────────────────────────────────────

    def start_trace(self, agent_name: str, operation: str,
                    parent_trace: Optional[str] = None) -> TraceSpan:
        """Start a distributed trace span."""
        trace_id = parent_trace or uuid.uuid4().hex[:12]
        span = TraceSpan(
            trace_id=trace_id, agent_name=agent_name,
            operation=operation, start_time=time.time(),
        )
        self._traces[trace_id].append(span)
        return span

    def end_trace(self, span: TraceSpan, status: str = "ok"):
        span.end_time = time.time()
        span.duration_ms = round((span.end_time - span.start_time) * 1000, 1)
        span.status = status

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "span_id": s.span_id, "agent": s.agent_name,
                "operation": s.operation, "duration_ms": s.duration_ms,
                "status": s.status, "parent": s.parent_span,
            }
            for s in self._traces.get(trace_id, [])
        ]

    # ── SLA Tracking ──────────────────────────────────────────────────

    def get_sla_compliance(self) -> Dict[str, Any]:
        compliance = {}
        for name, targets in self._sla_targets.items():
            state = self._agents.get(name)
            if not state:
                continue
            checks = {}
            rt = targets.get("response_time_ms", 0)
            if rt:
                checks["response_time"] = {
                    "target_ms": rt, "actual_ms": state.avg_task_duration_ms,
                    "compliant": state.avg_task_duration_ms <= rt,
                }
            acc = targets.get("accuracy_pct", 0)
            if acc:
                checks["accuracy"] = {
                    "target_pct": acc, "actual_pct": state.success_rate,
                    "compliant": state.success_rate >= acc,
                }
            compliance[name] = {
                "checks": checks,
                "overall_compliant": all(c["compliant"] for c in checks.values()),
            }
        return compliance

    # ── Dashboard Data ────────────────────────────────────────────────

    def get_all_status(self) -> Dict[str, Any]:
        return {
            "agents": {
                name: {
                    "status": s.status,
                    "last_heartbeat": s.last_heartbeat,
                    "current_task": s.current_task,
                    "queue_depth": s.queue_depth,
                    "total_tasks": s.total_tasks,
                    "success_rate": s.success_rate,
                    "avg_duration_ms": s.avg_task_duration_ms,
                    "error_count": s.error_count,
                    "cpu_percent": s.cpu_percent,
                    "memory_mb": s.memory_mb,
                    "uptime_hours": round(s.uptime_sec / 3600, 1),
                }
                for name, s in self._agents.items()
            },
            "alerts": [
                {"id": a.id, "agent": a.agent_name, "type": a.alert_type,
                 "severity": a.severity, "message": a.message,
                 "timestamp": a.timestamp, "resolved": a.resolved}
                for a in self._alerts[-20:]
            ],
            "sla_compliance": self.get_sla_compliance(),
        }

    @property
    def stats(self) -> Dict[str, Any]:
        statuses = [s.status for s in self._agents.values()]
        return {
            "total_agents": len(self._agents),
            "healthy": statuses.count("healthy"),
            "degraded": statuses.count("degraded"),
            "unhealthy": statuses.count("unhealthy"),
            "total_alerts": len(self._alerts),
            "unresolved_alerts": sum(1 for a in self._alerts if not a.resolved),
        }
