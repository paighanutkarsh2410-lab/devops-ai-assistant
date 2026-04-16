"""
Chaos Engineering Suite: Controlled failure injection to test system resilience.
Implements chaos experiments with safety controls, monitoring, and auto-rollback.
"""
import logging
import os
import random
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ChaosState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class ChaosExperiment:
    name: str
    category: str  # service, network, resource, database, agent
    description: str
    severity: str  # low, medium, high, critical
    duration_seconds: int = 300
    state: str = ChaosState.PENDING
    started_at: str = ""
    completed_at: str = ""
    inject_fn: Optional[Callable] = None
    rollback_fn: Optional[Callable] = None
    results: Dict[str, Any] = field(default_factory=dict)
    agent_detected: bool = False
    agent_diagnosed: bool = False
    agent_remediated: bool = False
    detection_time_ms: float = 0
    recovery_time_ms: float = 0


@dataclass
class SafetyControls:
    max_blast_radius: int = 1           # Max services affected simultaneously
    require_approval: bool = True       # Require manual approval before running
    auto_rollback_seconds: int = 600    # Force rollback after this duration
    business_hours_only: bool = False   # Only run during business hours
    excluded_services: List[str] = field(default_factory=lambda: ["database-primary", "auth-service"])
    emergency_stop: bool = False        # Kill switch


class ChaosSuite:
    """
    Controlled chaos engineering framework with safety controls.
    Tests system resilience by injecting failures and monitoring response.
    """

    def __init__(self, safety: SafetyControls = None):
        self.safety = safety or SafetyControls()
        self._experiments: List[ChaosExperiment] = []
        self._active: Optional[ChaosExperiment] = None
        self._history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._register_experiments()

    def _register_experiments(self):
        """Register all chaos experiments."""
        self._experiments = [
            # Service chaos
            ChaosExperiment(
                name="kill_random_service",
                category="service",
                description="Kill a random non-critical service and observe recovery",
                severity="high",
                duration_seconds=300,
                inject_fn=self._chaos_kill_service,
                rollback_fn=self._rollback_kill_service,
            ),
            ChaosExperiment(
                name="restart_api_server",
                category="service",
                description="Restart API server to test zero-downtime deployment",
                severity="medium",
                duration_seconds=60,
                inject_fn=self._chaos_restart_api,
                rollback_fn=self._rollback_restart_api,
            ),

            # Network chaos
            ChaosExperiment(
                name="network_latency",
                category="network",
                description="Introduce 500ms network latency to simulate degraded connectivity",
                severity="medium",
                duration_seconds=300,
                inject_fn=self._chaos_network_latency,
                rollback_fn=self._rollback_network_latency,
            ),
            ChaosExperiment(
                name="packet_loss",
                category="network",
                description="Simulate 10% packet loss on network interface",
                severity="high",
                duration_seconds=180,
                inject_fn=self._chaos_packet_loss,
                rollback_fn=self._rollback_packet_loss,
            ),
            ChaosExperiment(
                name="dns_failure",
                category="network",
                description="Simulate DNS resolution failure",
                severity="high",
                duration_seconds=120,
                inject_fn=self._chaos_dns_failure,
                rollback_fn=self._rollback_dns_failure,
            ),

            # Resource chaos
            ChaosExperiment(
                name="cpu_spike",
                category="resource",
                description="Max out CPU to test performance under resource contention",
                severity="medium",
                duration_seconds=300,
                inject_fn=self._chaos_cpu_spike,
                rollback_fn=self._rollback_cpu_spike,
            ),
            ChaosExperiment(
                name="memory_pressure",
                category="resource",
                description="Allocate memory to trigger OOM pressure",
                severity="high",
                duration_seconds=180,
                inject_fn=self._chaos_memory_pressure,
                rollback_fn=self._rollback_memory_pressure,
            ),
            ChaosExperiment(
                name="disk_fill",
                category="resource",
                description="Fill disk to 95% to test disk space handling",
                severity="high",
                duration_seconds=300,
                inject_fn=self._chaos_disk_fill,
                rollback_fn=self._rollback_disk_fill,
            ),

            # Database chaos
            ChaosExperiment(
                name="database_connection_drop",
                category="database",
                description="Pause database to simulate connection failure",
                severity="critical",
                duration_seconds=60,
                inject_fn=self._chaos_database_failure,
                rollback_fn=self._rollback_database_failure,
            ),
            ChaosExperiment(
                name="database_slow_queries",
                category="database",
                description="Introduce artificial query latency",
                severity="medium",
                duration_seconds=300,
                inject_fn=self._chaos_slow_queries,
                rollback_fn=self._rollback_slow_queries,
            ),

            # Agent chaos
            ChaosExperiment(
                name="agent_crash",
                category="agent",
                description="Kill a random agent process to test agent recovery",
                severity="medium",
                duration_seconds=120,
                inject_fn=self._chaos_agent_crash,
                rollback_fn=self._rollback_agent_crash,
            ),
            ChaosExperiment(
                name="agent_overload",
                category="agent",
                description="Flood agents with events to test queue management",
                severity="medium",
                duration_seconds=180,
                inject_fn=self._chaos_agent_overload,
                rollback_fn=self._rollback_agent_overload,
            ),
        ]

    def emergency_stop(self):
        """Emergency stop — immediately rollback all active experiments."""
        self.safety.emergency_stop = True
        if self._active and self._active.rollback_fn:
            logger.critical("EMERGENCY STOP — rolling back active experiment")
            try:
                self._active.rollback_fn()
            except Exception as e:
                logger.error(f"Rollback failed: {e}")
            self._active.state = ChaosState.ABORTED
            self._active.completed_at = datetime.now(timezone.utc).isoformat()
        self._active = None

    def run_experiment(self, experiment_name: str, approved: bool = False) -> Dict[str, Any]:
        """Run a specific chaos experiment with safety checks."""
        if self.safety.emergency_stop:
            return {"error": "Emergency stop active — all experiments halted"}

        exp = next((e for e in self._experiments if e.name == experiment_name), None)
        if not exp:
            return {"error": f"Unknown experiment: {experiment_name}"}

        # Safety checks
        if self.safety.require_approval and not approved:
            return {"error": "Experiment requires approval", "experiment": exp.name, "severity": exp.severity}

        if self._active:
            return {"error": f"Experiment already running: {self._active.name}"}

        if exp.severity == "critical" and experiment_name in [s for s in self.safety.excluded_services]:
            return {"error": f"Experiment targets excluded service"}

        # Run experiment
        exp.state = ChaosState.RUNNING
        exp.started_at = datetime.now(timezone.utc).isoformat()
        self._active = exp
        start_time = time.time()

        result = {"experiment": exp.name, "category": exp.category, "severity": exp.severity}

        try:
            # Inject chaos
            if exp.inject_fn:
                inject_result = exp.inject_fn()
                result["inject"] = inject_result or "injected"

            # Monitor during experiment (simulated)
            monitor_data = self._monitor_during_experiment(exp)
            result["monitoring"] = monitor_data

            # Auto-rollback after duration
            time.sleep(min(exp.duration_seconds, 5))  # Shortened for demo

            # Rollback
            if exp.rollback_fn:
                exp.rollback_fn()
                result["rollback"] = "completed"

            exp.state = ChaosState.COMPLETED
            exp.recovery_time_ms = (time.time() - start_time) * 1000

        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            if exp.rollback_fn:
                try:
                    exp.rollback_fn()
                except Exception:
                    pass
            exp.state = ChaosState.FAILED
            result["error"] = str(e)

        exp.completed_at = datetime.now(timezone.utc).isoformat()
        self._active = None

        # Evaluate agent response
        result["agent_response"] = {
            "detected": exp.agent_detected,
            "diagnosed": exp.agent_diagnosed,
            "remediated": exp.agent_remediated,
            "detection_time_ms": exp.detection_time_ms,
            "recovery_time_ms": exp.recovery_time_ms,
        }

        self._history.append(result)
        return result

    def _monitor_during_experiment(self, exp: ChaosExperiment) -> Dict[str, Any]:
        """Simulate monitoring during chaos experiment."""
        # In production, this would query real monitoring endpoints
        exp.agent_detected = random.random() > 0.15       # 85% detection rate
        exp.agent_diagnosed = random.random() > 0.25       # 75% diagnosis rate
        exp.agent_remediated = random.random() > 0.35      # 65% remediation rate
        exp.detection_time_ms = random.uniform(500, 15000)

        return {
            "health_checks_failed": random.randint(0, 5),
            "error_rate_spike": round(random.uniform(0, 0.15), 3),
            "latency_increase_ms": round(random.uniform(50, 500), 1),
            "alerts_generated": random.randint(1, 8),
            "affected_services": random.randint(1, 3),
        }

    # ── Chaos Injection Functions ─────────────────────────────────────

    def _chaos_kill_service(self):
        services = ["backend-worker", "redis-cache", "agent-monitor"]
        target = random.choice(services)
        logger.info(f"CHAOS: Killing service {target}")
        # subprocess.run(["docker", "kill", target], capture_output=True)
        return {"killed": target}

    def _rollback_kill_service(self):
        logger.info("ROLLBACK: Restarting killed service")
        # subprocess.run(["docker", "start", target], capture_output=True)

    def _chaos_restart_api(self):
        logger.info("CHAOS: Restarting API server")
        return {"restarted": "api-server"}

    def _rollback_restart_api(self):
        logger.info("ROLLBACK: API server restart rollback (no-op, already restarted)")

    def _chaos_network_latency(self):
        logger.info("CHAOS: Adding 500ms network latency")
        # subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "root", "netem", "delay", "500ms"])
        return {"latency_ms": 500, "interface": "eth0"}

    def _rollback_network_latency(self):
        logger.info("ROLLBACK: Removing network latency")
        # subprocess.run(["tc", "qdisc", "del", "dev", "eth0", "root"])

    def _chaos_packet_loss(self):
        logger.info("CHAOS: Introducing 10% packet loss")
        return {"packet_loss": "10%"}

    def _rollback_packet_loss(self):
        logger.info("ROLLBACK: Removing packet loss")

    def _chaos_dns_failure(self):
        logger.info("CHAOS: Simulating DNS failure")
        return {"dns": "blocked"}

    def _rollback_dns_failure(self):
        logger.info("ROLLBACK: Restoring DNS")

    def _chaos_cpu_spike(self):
        logger.info("CHAOS: CPU spike (4 cores)")
        # subprocess.run(["stress", "--cpu", "4", "--timeout", "300s"])
        return {"cpu_cores": 4, "duration": 300}

    def _rollback_cpu_spike(self):
        logger.info("ROLLBACK: CPU stress stopped")
        # subprocess.run(["pkill", "stress"])

    def _chaos_memory_pressure(self):
        logger.info("CHAOS: Memory pressure (1GB allocation)")
        return {"memory_mb": 1024}

    def _rollback_memory_pressure(self):
        logger.info("ROLLBACK: Memory released")

    def _chaos_disk_fill(self):
        logger.info("CHAOS: Filling disk to 95%")
        # subprocess.run(["dd", "if=/dev/zero", "of=/tmp/chaos_fill", "bs=1M", "count=1000"])
        return {"fill_target": "95%"}

    def _rollback_disk_fill(self):
        logger.info("ROLLBACK: Cleaning up disk fill")
        # os.remove("/tmp/chaos_fill")

    def _chaos_database_failure(self):
        logger.info("CHAOS: Pausing database")
        # subprocess.run(["docker", "pause", "postgres"])
        return {"database": "paused"}

    def _rollback_database_failure(self):
        logger.info("ROLLBACK: Unpausing database")
        # subprocess.run(["docker", "unpause", "postgres"])

    def _chaos_slow_queries(self):
        logger.info("CHAOS: Introducing query latency")
        return {"query_delay_ms": 500}

    def _rollback_slow_queries(self):
        logger.info("ROLLBACK: Removing query latency")

    def _chaos_agent_crash(self):
        agents = ["monitor_agent", "diagnostic_agent", "remediation_agent"]
        target = random.choice(agents)
        logger.info(f"CHAOS: Crashing agent {target}")
        return {"crashed_agent": target}

    def _rollback_agent_crash(self):
        logger.info("ROLLBACK: Restarting agent")

    def _chaos_agent_overload(self):
        logger.info("CHAOS: Flooding agent event queue")
        return {"events_injected": 10000}

    def _rollback_agent_overload(self):
        logger.info("ROLLBACK: Clearing agent queue")

    # ── Reporting ─────────────────────────────────────────────────────

    def get_resilience_score(self) -> Dict[str, Any]:
        """Calculate overall system resilience score from experiment history."""
        if not self._history:
            return {"score": 0, "experiments_run": 0, "message": "No experiments run yet"}

        total = len(self._history)
        detected = sum(1 for h in self._history if h.get("agent_response", {}).get("detected", False))
        diagnosed = sum(1 for h in self._history if h.get("agent_response", {}).get("diagnosed", False))
        remediated = sum(1 for h in self._history if h.get("agent_response", {}).get("remediated", False))
        successful = sum(1 for h in self._history if h.get("rollback") == "completed")

        detection_rate = detected / total if total else 0
        diagnosis_rate = diagnosed / total if total else 0
        remediation_rate = remediated / total if total else 0
        recovery_rate = successful / total if total else 0

        # Weighted score: detection 25%, diagnosis 25%, remediation 30%, recovery 20%
        score = (detection_rate * 25 + diagnosis_rate * 25 +
                 remediation_rate * 30 + recovery_rate * 20)

        return {
            "score": round(score, 1),
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
            "experiments_run": total,
            "detection_rate": round(detection_rate * 100, 1),
            "diagnosis_rate": round(diagnosis_rate * 100, 1),
            "remediation_rate": round(remediation_rate * 100, 1),
            "recovery_rate": round(recovery_rate * 100, 1),
            "avg_detection_time_ms": round(
                sum(h.get("agent_response", {}).get("detection_time_ms", 0) for h in self._history) / total, 0
            ),
        }

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all available experiments."""
        return [
            {
                "name": e.name,
                "category": e.category,
                "description": e.description,
                "severity": e.severity,
                "duration_seconds": e.duration_seconds,
                "state": e.state,
            }
            for e in self._experiments
        ]

    def get_history(self) -> List[Dict[str, Any]]:
        """Get experiment execution history."""
        return self._history
