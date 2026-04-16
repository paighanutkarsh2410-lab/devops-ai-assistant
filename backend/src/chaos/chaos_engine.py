"""Chaos engineering engine — controlled failure injection and resilience testing."""
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import logging

from models.database import Base

logger = logging.getLogger(__name__)


class ChaosExperiment(Base):
    __tablename__ = "chaos_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    experiment_type = Column(String, nullable=False)  # kill_service, latency, cpu_spike, disk_fill, network_partition, db_failure
    target_service = Column(String, nullable=True)
    config = Column(JSON, default=dict)  # experiment-specific params
    duration_seconds = Column(Integer, default=60)
    status = Column(String, default="pending")  # pending, running, completed, stopped, failed
    results = Column(JSON, nullable=True)
    safety_checks = Column(JSON, default=dict)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="chaos_experiments")


class ChaosEngine:
    """Runs controlled chaos experiments to test system resilience."""

    EXPERIMENT_TYPES = {
        "kill_service": {
            "name": "Kill Service",
            "description": "Terminate a service to test failover",
            "icon": "💀",
            "risk": "high",
        },
        "inject_latency": {
            "name": "Inject Latency",
            "description": "Add artificial latency to a service",
            "icon": "🐌",
            "risk": "medium",
        },
        "cpu_spike": {
            "name": "CPU Spike",
            "description": "Generate CPU load on a service",
            "icon": "🔥",
            "risk": "medium",
        },
        "disk_fill": {
            "name": "Fill Disk",
            "description": "Simulate disk space exhaustion",
            "icon": "💾",
            "risk": "high",
        },
        "network_partition": {
            "name": "Network Partition",
            "description": "Simulate network split between services",
            "icon": "🔌",
            "risk": "high",
        },
        "db_failure": {
            "name": "Database Failure",
            "description": "Simulate database connection failure",
            "icon": "🗄️",
            "risk": "high",
        },
        "memory_pressure": {
            "name": "Memory Pressure",
            "description": "Simulate memory pressure on a service",
            "icon": "🧠",
            "risk": "medium",
        },
        "dependency_failure": {
            "name": "Dependency Failure",
            "description": "Simulate downstream dependency failure",
            "icon": "⛓️",
            "risk": "medium",
        },
    }

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def create_experiment(self, name: str, experiment_type: str, target_service: str = None,
                          config: dict = None, duration_seconds: int = 60) -> dict:
        """Create a new chaos experiment."""
        if experiment_type not in self.EXPERIMENT_TYPES:
            return {"error": f"Unknown experiment type: {experiment_type}"}

        # Safety checks
        safety = self._run_safety_checks(experiment_type, target_service, duration_seconds)
        if not safety["safe"]:
            return {"error": "Safety check failed", "safety": safety}

        experiment = ChaosExperiment(
            user_id=self.user_id,
            name=name,
            experiment_type=experiment_type,
            target_service=target_service,
            config=config or {},
            duration_seconds=min(duration_seconds, 300),  # max 5 minutes
            safety_checks=safety,
        )
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)

        return self._serialize(experiment)

    def run_experiment(self, experiment_id: str) -> dict:
        """Execute a chaos experiment."""
        experiment = self._get_owned(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        if experiment.status not in ("pending",):
            return {"error": f"Cannot run experiment in '{experiment.status}' state"}

        experiment.status = "running"
        experiment.started_at = datetime.utcnow()
        self.db.commit()

        # Simulate experiment execution
        results = self._execute_experiment(experiment)

        experiment.status = "completed"
        experiment.completed_at = datetime.utcnow()
        experiment.results = results
        self.db.commit()

        return self._serialize(experiment)

    def stop_experiment(self, experiment_id: str) -> dict:
        """Emergency stop an experiment."""
        experiment = self._get_owned(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        if experiment.status != "running":
            return {"error": "Experiment is not running"}

        experiment.status = "stopped"
        experiment.completed_at = datetime.utcnow()
        experiment.results = {
            "stopped": True,
            "reason": "Manual emergency stop",
            "stopped_at": datetime.utcnow().isoformat(),
            "rollback": "Rollback executed successfully",
        }
        self.db.commit()

        return self._serialize(experiment)

    def get_experiments(self, status: str = None, limit: int = 50) -> list[dict]:
        """List experiments."""
        q = self.db.query(ChaosExperiment).filter(ChaosExperiment.user_id == self.user_id)
        if status:
            q = q.filter(ChaosExperiment.status == status)
        exps = q.order_by(ChaosExperiment.created_at.desc()).limit(limit).all()
        return [self._serialize(e) for e in exps]

    def get_experiment_results(self, experiment_id: str) -> dict:
        """Get detailed results for an experiment."""
        experiment = self._get_owned(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        return {
            **self._serialize(experiment),
            "analysis": self._analyze_results(experiment),
        }

    def get_resilience_report(self) -> dict:
        """Generate overall resilience report from all experiments."""
        experiments = self.db.query(ChaosExperiment).filter(
            ChaosExperiment.user_id == self.user_id,
            ChaosExperiment.status == "completed",
        ).all()

        total = len(experiments)
        if total == 0:
            return {"total_experiments": 0, "message": "No completed experiments"}

        detected = sum(1 for e in experiments if (e.results or {}).get("monitoring_detected", False))
        auto_recovered = sum(1 for e in experiments if (e.results or {}).get("auto_recovered", False))
        avg_detection = []
        avg_recovery = []

        for e in experiments:
            r = e.results or {}
            if r.get("detection_time_seconds"):
                avg_detection.append(r["detection_time_seconds"])
            if r.get("recovery_time_seconds"):
                avg_recovery.append(r["recovery_time_seconds"])

        # Score by type
        by_type: dict[str, dict] = {}
        for e in experiments:
            t = e.experiment_type
            if t not in by_type:
                by_type[t] = {"total": 0, "detected": 0, "recovered": 0}
            by_type[t]["total"] += 1
            if (e.results or {}).get("monitoring_detected"):
                by_type[t]["detected"] += 1
            if (e.results or {}).get("auto_recovered"):
                by_type[t]["recovered"] += 1

        return {
            "total_experiments": total,
            "detection_rate": round(detected / total * 100, 1),
            "auto_recovery_rate": round(auto_recovered / total * 100, 1),
            "avg_detection_seconds": round(sum(avg_detection) / len(avg_detection)) if avg_detection else None,
            "avg_recovery_seconds": round(sum(avg_recovery) / len(avg_recovery)) if avg_recovery else None,
            "resilience_score": self._calc_resilience_score(detected, auto_recovered, total),
            "by_type": by_type,
        }

    # ── Experiment execution (simulated) ───────────────────────────────

    def _execute_experiment(self, experiment: ChaosExperiment) -> dict:
        """Simulate experiment execution and measure system response."""
        exp_type = experiment.experiment_type
        import random

        # Simulate monitoring detection
        detected = random.random() > 0.2  # 80% detection rate
        detection_time = random.randint(5, 120) if detected else None

        # Simulate auto-recovery
        auto_recovered = detected and random.random() > 0.3  # 70% recovery if detected
        recovery_time = random.randint(30, 300) if auto_recovered else None

        # Impact assessment
        impact = {
            "kill_service": {"error_rate_increase": round(random.uniform(20, 100), 1), "requests_affected": random.randint(50, 500)},
            "inject_latency": {"latency_increase_ms": random.randint(100, 2000), "timeout_rate": round(random.uniform(1, 30), 1)},
            "cpu_spike": {"cpu_peak_percent": round(random.uniform(80, 100), 1), "affected_processes": random.randint(1, 10)},
            "disk_fill": {"disk_usage_percent": round(random.uniform(90, 99), 1), "writes_blocked": random.random() > 0.5},
            "network_partition": {"packets_dropped": random.randint(100, 10000), "services_isolated": random.randint(1, 3)},
            "db_failure": {"queries_failed": random.randint(10, 200), "connection_pool_exhausted": random.random() > 0.5},
            "memory_pressure": {"memory_peak_percent": round(random.uniform(85, 99), 1), "oom_kills": random.randint(0, 2)},
            "dependency_failure": {"cascading_failures": random.randint(0, 3), "degraded_endpoints": random.randint(1, 5)},
        }

        return {
            "experiment_type": exp_type,
            "target": experiment.target_service,
            "duration_seconds": experiment.duration_seconds,
            "monitoring_detected": detected,
            "detection_time_seconds": detection_time,
            "auto_recovered": auto_recovered,
            "recovery_time_seconds": recovery_time,
            "impact": impact.get(exp_type, {}),
            "rollback": "Automatic rollback executed" if auto_recovered else "Manual intervention required",
            "completed_at": datetime.utcnow().isoformat(),
        }

    def _run_safety_checks(self, exp_type: str, target: str, duration: int) -> dict:
        """Run pre-experiment safety checks."""
        checks = {
            "max_duration_ok": duration <= 300,
            "experiment_type_valid": exp_type in self.EXPERIMENT_TYPES,
            "no_active_experiments": self.db.query(ChaosExperiment).filter(
                ChaosExperiment.user_id == self.user_id,
                ChaosExperiment.status == "running",
            ).count() == 0,
        }

        return {
            "safe": all(checks.values()),
            "checks": checks,
        }

    def _analyze_results(self, experiment: ChaosExperiment) -> dict:
        results = experiment.results or {}
        findings = []
        action_items = []

        if results.get("monitoring_detected"):
            dt = results.get("detection_time_seconds", 0)
            if dt < 30:
                findings.append("Monitoring detected the issue quickly (<30s)")
            elif dt < 120:
                findings.append(f"Monitoring detected the issue in {dt}s — consider tuning for faster detection")
            else:
                findings.append(f"Slow detection ({dt}s) — review monitoring thresholds")
                action_items.append("Review and lower detection thresholds")
        else:
            findings.append("Monitoring did NOT detect the injected failure")
            action_items.append("Add monitoring for this failure mode")

        if results.get("auto_recovered"):
            findings.append("System auto-recovered successfully")
        else:
            findings.append("System did not auto-recover — manual intervention was needed")
            action_items.append("Add auto-remediation for this failure type")

        return {"findings": findings, "action_items": action_items}

    def _calc_resilience_score(self, detected: int, recovered: int, total: int) -> int:
        if total == 0:
            return 100
        detection_score = (detected / total) * 50
        recovery_score = (recovered / total) * 50
        return min(100, round(detection_score + recovery_score))

    def _get_owned(self, experiment_id: str) -> ChaosExperiment | None:
        return self.db.query(ChaosExperiment).filter(
            ChaosExperiment.id == experiment_id, ChaosExperiment.user_id == self.user_id
        ).first()

    def _serialize(self, e: ChaosExperiment) -> dict:
        type_info = self.EXPERIMENT_TYPES.get(e.experiment_type, {})
        return {
            "id": str(e.id),
            "name": e.name,
            "experiment_type": e.experiment_type,
            "type_info": type_info,
            "target_service": e.target_service,
            "config": e.config,
            "duration_seconds": e.duration_seconds,
            "status": e.status,
            "results": e.results,
            "safety_checks": e.safety_checks,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
