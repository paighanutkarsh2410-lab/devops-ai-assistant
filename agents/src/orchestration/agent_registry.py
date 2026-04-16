"""
Agent Registry: Tracks all available agents, their capabilities, load, and health.
"""
import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    name: str
    description: str
    domains: List[str]  # e.g. ["database", "memory", "network"]
    actions: List[str]  # e.g. ["diagnose", "remediate", "predict"]
    priority: int = 5  # 1=highest, 10=lowest


@dataclass
class AgentEntry:
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    current_tasks: int = 0
    max_concurrent_tasks: int = 3
    total_tasks_completed: int = 0
    total_successes: int = 0
    total_failures: int = 0
    avg_response_time_ms: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    last_error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        total = self.total_successes + self.total_failures
        return (self.total_successes / total * 100) if total > 0 else 100.0

    @property
    def load_factor(self) -> float:
        return self.current_tasks / max(self.max_concurrent_tasks, 1)

    @property
    def is_available(self) -> bool:
        return (
            self.status in (AgentStatus.IDLE, AgentStatus.BUSY)
            and self.current_tasks < self.max_concurrent_tasks
        )


class AgentRegistry:
    """Central registry for all agents in the system."""

    def __init__(self):
        self._agents: Dict[str, AgentEntry] = {}
        self._lock = threading.Lock()
        self._health_check_interval = 60  # seconds

    def register(self, agent_id: str, agent_type: str,
                 capabilities: List[AgentCapability] = None,
                 max_concurrent: int = 3) -> AgentEntry:
        with self._lock:
            entry = AgentEntry(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities or [],
                max_concurrent_tasks=max_concurrent,
            )
            self._agents[agent_id] = entry
            logger.info(f"[Registry] Registered agent: {agent_id} ({agent_type})")
            return entry

    def unregister(self, agent_id: str):
        with self._lock:
            self._agents.pop(agent_id, None)
            logger.info(f"[Registry] Unregistered agent: {agent_id}")

    def heartbeat(self, agent_id: str, status: AgentStatus = None):
        with self._lock:
            entry = self._agents.get(agent_id)
            if entry:
                entry.last_heartbeat = time.time()
                if status:
                    entry.status = status

    def acquire_task(self, agent_id: str) -> bool:
        with self._lock:
            entry = self._agents.get(agent_id)
            if not entry or not entry.is_available:
                return False
            entry.current_tasks += 1
            if entry.current_tasks >= entry.max_concurrent_tasks:
                entry.status = AgentStatus.OVERLOADED
            elif entry.current_tasks > 0:
                entry.status = AgentStatus.BUSY
            return True

    def release_task(self, agent_id: str, success: bool = True,
                     response_time_ms: float = 0, error: str = None):
        with self._lock:
            entry = self._agents.get(agent_id)
            if not entry:
                return
            entry.current_tasks = max(0, entry.current_tasks - 1)
            entry.total_tasks_completed += 1
            if success:
                entry.total_successes += 1
            else:
                entry.total_failures += 1
                entry.last_error = error
            # Running average response time
            n = entry.total_tasks_completed
            entry.avg_response_time_ms = (
                entry.avg_response_time_ms * (n - 1) + response_time_ms
            ) / n
            # Update status
            if entry.current_tasks == 0:
                entry.status = AgentStatus.IDLE
            elif entry.current_tasks < entry.max_concurrent_tasks:
                entry.status = AgentStatus.BUSY

    def find_agents_for_domain(self, domain: str) -> List[AgentEntry]:
        """Find all available agents that handle a given domain."""
        results = []
        with self._lock:
            for entry in self._agents.values():
                if not entry.is_available:
                    continue
                for cap in entry.capabilities:
                    if domain in cap.domains:
                        results.append(entry)
                        break
        # Sort by load (least loaded first), then by success rate (highest first)
        results.sort(key=lambda a: (a.load_factor, -a.success_rate))
        return results

    def find_agents_for_action(self, action: str) -> List[AgentEntry]:
        results = []
        with self._lock:
            for entry in self._agents.values():
                if not entry.is_available:
                    continue
                for cap in entry.capabilities:
                    if action in cap.actions:
                        results.append(entry)
                        break
        results.sort(key=lambda a: (a.load_factor, -a.success_rate))
        return results

    def get_best_agent(self, domain: str = None, action: str = None) -> Optional[AgentEntry]:
        if domain:
            agents = self.find_agents_for_domain(domain)
        elif action:
            agents = self.find_agents_for_action(action)
        else:
            agents = [a for a in self._agents.values() if a.is_available]
        return agents[0] if agents else None

    def get_all(self) -> List[AgentEntry]:
        with self._lock:
            return list(self._agents.values())

    def get_status(self, agent_id: str) -> Optional[AgentEntry]:
        return self._agents.get(agent_id)

    def check_health(self):
        """Mark agents with stale heartbeats as unhealthy."""
        now = time.time()
        with self._lock:
            for entry in self._agents.values():
                if now - entry.last_heartbeat > self._health_check_interval * 2:
                    entry.status = AgentStatus.OFFLINE
                elif now - entry.last_heartbeat > self._health_check_interval:
                    entry.status = AgentStatus.UNHEALTHY

    def get_registry_stats(self) -> dict:
        with self._lock:
            agents = list(self._agents.values())
        total = len(agents)
        available = sum(1 for a in agents if a.is_available)
        busy = sum(1 for a in agents if a.status == AgentStatus.BUSY)
        total_tasks = sum(a.current_tasks for a in agents)
        avg_success = (
            sum(a.success_rate for a in agents) / total if total > 0 else 0
        )
        return {
            "total_agents": total,
            "available": available,
            "busy": busy,
            "total_active_tasks": total_tasks,
            "avg_success_rate": round(avg_success, 1),
            "agents": [
                {
                    "id": a.agent_id,
                    "type": a.agent_type,
                    "status": a.status.value,
                    "load": round(a.load_factor, 2),
                    "success_rate": round(a.success_rate, 1),
                    "tasks_completed": a.total_tasks_completed,
                    "avg_response_ms": round(a.avg_response_time_ms, 1),
                }
                for a in agents
            ],
        }
