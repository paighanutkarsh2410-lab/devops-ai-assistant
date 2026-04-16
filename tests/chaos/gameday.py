"""
Game Day: Organized chaos engineering exercise with multi-failure scenarios.
Simulates real-world incidents for team response drill and learning.
"""
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class GameDayScenario:
    name: str
    description: str
    difficulty: str  # easy, medium, hard, extreme
    experiments: List[str]  # Chaos experiment names to run
    expected_impact: str
    success_criteria: List[str]
    time_limit_minutes: int = 30


@dataclass
class GameDayResult:
    scenario_name: str
    started_at: str
    completed_at: str
    duration_minutes: float
    experiments_run: int
    incidents_detected: int
    incidents_resolved: int
    mean_detection_time_s: float
    mean_recovery_time_s: float
    success_criteria_met: List[Dict[str, Any]]
    team_score: float
    lessons_learned: List[str] = field(default_factory=list)


class GameDay:
    """
    Organized chaos exercise — multiple simultaneous failures,
    team response drill, and learning exercise.
    """

    SCENARIOS = [
        GameDayScenario(
            name="Cascading Service Failure",
            description="Backend worker dies, causing queue backup and downstream timeouts",
            difficulty="medium",
            experiments=["kill_random_service", "network_latency"],
            expected_impact="Partial service degradation, increased latency",
            success_criteria=[
                "Monitor agent detects failure within 60 seconds",
                "Diagnostic agent identifies root cause",
                "Remediation agent restarts failed service",
                "System recovers within 5 minutes",
            ],
            time_limit_minutes=15,
        ),
        GameDayScenario(
            name="Database Under Pressure",
            description="Database connections drop while slow queries pile up",
            difficulty="hard",
            experiments=["database_connection_drop", "database_slow_queries", "cpu_spike"],
            expected_impact="API errors, data access failures, dashboard degradation",
            success_criteria=[
                "Connection pool handles graceful degradation",
                "Circuit breaker activates for database calls",
                "Cached data served during outage",
                "Full recovery after database restored",
            ],
            time_limit_minutes=20,
        ),
        GameDayScenario(
            name="Resource Exhaustion Storm",
            description="CPU spike + memory pressure + disk filling simultaneously",
            difficulty="extreme",
            experiments=["cpu_spike", "memory_pressure", "disk_fill"],
            expected_impact="System-wide performance degradation, potential OOM kills",
            success_criteria=[
                "Agents detect resource exhaustion",
                "Auto-scaling triggered or recommended",
                "Non-essential services gracefully shed load",
                "Core functionality remains available",
                "Recovery within 10 minutes of resource release",
            ],
            time_limit_minutes=30,
        ),
        GameDayScenario(
            name="Network Partition",
            description="Network latency spikes with packet loss — simulates cloud region issues",
            difficulty="hard",
            experiments=["network_latency", "packet_loss", "dns_failure"],
            expected_impact="Timeouts, retries, potential split-brain",
            success_criteria=[
                "Timeout handling prevents cascading failures",
                "Retry logic with exponential backoff activates",
                "Health checks detect network degradation",
                "System recovers when network restored",
            ],
            time_limit_minutes=20,
        ),
        GameDayScenario(
            name="Agent Swarm Failure",
            description="Multiple agents crash simultaneously — tests agent orchestration",
            difficulty="medium",
            experiments=["agent_crash", "agent_overload"],
            expected_impact="Delayed incident detection and response",
            success_criteria=[
                "Orchestrator detects agent failures",
                "Failed agents auto-restart",
                "Event queue preserved during outage",
                "No duplicate processing after recovery",
            ],
            time_limit_minutes=15,
        ),
    ]

    def __init__(self):
        self._results: List[GameDayResult] = []

    def run_scenario(self, scenario_name: str) -> GameDayResult:
        """Run a game day scenario (simulated)."""
        scenario = next((s for s in self.SCENARIOS if s.name == scenario_name), None)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        started = datetime.now(timezone.utc)
        logger.info(f"GAME DAY: Starting '{scenario.name}' ({scenario.difficulty})")

        # Simulate running experiments and observing response
        detection_times = []
        recovery_times = []
        detected = 0
        resolved = 0

        for exp_name in scenario.experiments:
            # Simulate detection
            det_time = random.uniform(2, 60)
            detection_times.append(det_time)
            if random.random() > 0.1:  # 90% detection rate
                detected += 1

            # Simulate recovery
            rec_time = random.uniform(10, 300)
            recovery_times.append(rec_time)
            if random.random() > 0.2:  # 80% resolution rate
                resolved += 1

        # Evaluate success criteria
        criteria_results = []
        for criterion in scenario.success_criteria:
            met = random.random() > 0.2  # 80% success rate in simulation
            criteria_results.append({"criterion": criterion, "met": met})

        criteria_met = sum(1 for c in criteria_results if c["met"])
        total_criteria = len(criteria_results)

        completed = datetime.now(timezone.utc)
        duration = (completed - started).total_seconds() / 60

        # Score: weighted by criteria met, detection speed, recovery speed
        score = (criteria_met / total_criteria * 60 +
                 (detected / len(scenario.experiments)) * 20 +
                 (resolved / len(scenario.experiments)) * 20)

        result = GameDayResult(
            scenario_name=scenario.name,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
            duration_minutes=round(duration, 1),
            experiments_run=len(scenario.experiments),
            incidents_detected=detected,
            incidents_resolved=resolved,
            mean_detection_time_s=round(sum(detection_times) / len(detection_times), 1) if detection_times else 0,
            mean_recovery_time_s=round(sum(recovery_times) / len(recovery_times), 1) if recovery_times else 0,
            success_criteria_met=criteria_results,
            team_score=round(score, 1),
            lessons_learned=self._generate_lessons(scenario, criteria_results),
        )

        self._results.append(result)
        return result

    def _generate_lessons(self, scenario: GameDayScenario,
                          criteria: List[Dict]) -> List[str]:
        """Generate lessons learned from game day results."""
        lessons = []
        failed = [c["criterion"] for c in criteria if not c["met"]]

        if failed:
            for f in failed[:3]:
                lessons.append(f"Improvement needed: {f}")

        if scenario.difficulty in ("hard", "extreme"):
            lessons.append("Consider adding automated runbook for this scenario")

        lessons.append("Update incident response playbook with findings")
        lessons.append("Schedule follow-up drill in 30 days")

        return lessons

    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """List all available game day scenarios."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "difficulty": s.difficulty,
                "experiments": s.experiments,
                "expected_impact": s.expected_impact,
                "success_criteria": s.success_criteria,
                "time_limit_minutes": s.time_limit_minutes,
            }
            for s in self.SCENARIOS
        ]

    def get_history(self) -> List[Dict[str, Any]]:
        """Get game day execution history."""
        return [
            {
                "scenario_name": r.scenario_name,
                "started_at": r.started_at,
                "duration_minutes": r.duration_minutes,
                "team_score": r.team_score,
                "incidents_detected": r.incidents_detected,
                "incidents_resolved": r.incidents_resolved,
                "criteria_met": sum(1 for c in r.success_criteria_met if c["met"]),
                "criteria_total": len(r.success_criteria_met),
                "lessons_learned": r.lessons_learned,
            }
            for r in self._results
        ]
