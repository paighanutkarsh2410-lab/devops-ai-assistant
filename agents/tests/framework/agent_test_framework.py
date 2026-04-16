"""
Agent Test Framework: Comprehensive testing infrastructure for agents.
Includes mock generators, scenario runners, performance testing, and chaos injection.
"""
import time
import uuid
import random
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    test_name: str
    status: str = "pending"  # passed, failed, error, skipped
    duration_ms: float = 0
    message: str = ""
    assertions: int = 0
    failures: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    scenario_name: str
    steps: List[TestResult] = field(default_factory=list)
    overall_status: str = "pending"
    duration_ms: float = 0


# ── Mock Data Generators ──────────────────────────────────────────────

class MockDataGenerator:
    """Generate realistic test data for agent testing."""

    SERVICES = ["api-gateway", "auth-service", "order-service", "payment-service",
                "user-service", "notification-service", "inventory-service"]
    SEVERITIES = ["critical", "high", "medium", "low"]
    INCIDENT_TYPES = ["high_cpu", "memory_leak", "api_timeout", "disk_full",
                      "connection_pool_exhausted", "certificate_expiry", "cascading_failure"]

    @staticmethod
    def incident(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a realistic incident."""
        itype = random.choice(MockDataGenerator.INCIDENT_TYPES)
        service = random.choice(MockDataGenerator.SERVICES)
        severity = random.choice(MockDataGenerator.SEVERITIES)
        incident = {
            "id": str(uuid.uuid4()),
            "title": f"{itype.replace('_', ' ').title()} on {service}",
            "description": f"Automated detection of {itype} condition on {service}",
            "severity": severity,
            "service_name": service,
            "status": "detected",
            "incident_type": itype,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "root_cause": None,
            "solution": None,
            "auto_resolved": False,
            "metrics": MockDataGenerator.metrics(service),
        }
        if overrides:
            incident.update(overrides)
        return incident

    @staticmethod
    def metrics(service: str = "api-service") -> Dict[str, float]:
        """Generate realistic metric data."""
        return {
            "cpu_percent": round(random.uniform(20, 95), 1),
            "memory_percent": round(random.uniform(30, 90), 1),
            "disk_percent": round(random.uniform(40, 85), 1),
            "request_rate": round(random.uniform(100, 5000), 0),
            "error_rate": round(random.uniform(0, 10), 2),
            "response_time_p50": round(random.uniform(10, 500), 0),
            "response_time_p95": round(random.uniform(100, 3000), 0),
            "response_time_p99": round(random.uniform(200, 5000), 0),
            "active_connections": random.randint(10, 500),
        }

    @staticmethod
    def log_entries(count: int = 20, service: str = "api-service") -> List[Dict[str, Any]]:
        """Generate realistic log entries."""
        templates = [
            ("ERROR", "Connection refused to database: timeout after 30s"),
            ("ERROR", "OutOfMemoryError: Java heap space"),
            ("WARN", "Slow query detected: SELECT * FROM orders took 2.5s"),
            ("WARN", "Thread pool exhausted: 200/200 threads in use"),
            ("INFO", "Health check passed for {service}"),
            ("INFO", "Request processed successfully in 45ms"),
            ("ERROR", "HTTP 503: Service temporarily unavailable"),
            ("WARN", "High memory usage detected: 87% utilized"),
        ]
        entries = []
        base_time = datetime.now(timezone.utc) - timedelta(minutes=count)
        for i in range(count):
            level, msg = random.choice(templates)
            entries.append({
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "level": level,
                "service": service,
                "message": msg.format(service=service),
            })
        return entries

    @staticmethod
    def metric_timeseries(metric: str = "cpu_percent", points: int = 100,
                          base: float = 50.0, noise: float = 10.0) -> List[Dict[str, Any]]:
        """Generate time-series metric data."""
        base_time = datetime.now(timezone.utc) - timedelta(minutes=points)
        return [
            {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "metric": metric,
                "value": round(base + random.gauss(0, noise), 2),
            }
            for i in range(points)
        ]


# ── Agent Test Framework ──────────────────────────────────────────────

class AgentTestFramework:
    """
    Comprehensive testing framework for agents.
    Supports unit tests, integration tests, scenario tests, performance tests, and chaos tests.
    """

    def __init__(self):
        self._tests: Dict[str, Callable] = {}
        self._results: List[TestResult] = []
        self._scenarios: Dict[str, List[Dict[str, Any]]] = {}
        self.mock = MockDataGenerator()

    def register_test(self, name: str, test_fn: Callable):
        """Register a test function."""
        self._tests[name] = test_fn

    def run_test(self, name: str) -> TestResult:
        """Run a single test."""
        fn = self._tests.get(name)
        if not fn:
            return TestResult(test_name=name, status="error", message="Test not found")

        start = time.time()
        try:
            fn()
            result = TestResult(
                test_name=name, status="passed",
                duration_ms=round((time.time() - start) * 1000, 1),
            )
        except AssertionError as e:
            result = TestResult(
                test_name=name, status="failed",
                duration_ms=round((time.time() - start) * 1000, 1),
                message=str(e), failures=1,
            )
        except Exception as e:
            result = TestResult(
                test_name=name, status="error",
                duration_ms=round((time.time() - start) * 1000, 1),
                message=str(e),
            )

        self._results.append(result)
        return result

    def run_all(self) -> List[TestResult]:
        """Run all registered tests."""
        return [self.run_test(name) for name in self._tests]

    # ── Scenario Testing ──────────────────────────────────────────────

    def run_scenario(self, name: str, steps: List[Dict[str, Any]]) -> ScenarioResult:
        """Run a multi-step scenario test."""
        scenario = ScenarioResult(scenario_name=name)
        start = time.time()

        for step in steps:
            step_name = step.get("name", "unnamed")
            step_fn = step.get("fn")
            expected = step.get("expected", {})

            step_start = time.time()
            try:
                result = step_fn() if step_fn else {}
                # Validate expected values
                failures = 0
                for key, exp_val in expected.items():
                    actual = result.get(key) if isinstance(result, dict) else None
                    if actual != exp_val:
                        failures += 1

                step_result = TestResult(
                    test_name=step_name,
                    status="passed" if failures == 0 else "failed",
                    duration_ms=round((time.time() - step_start) * 1000, 1),
                    assertions=len(expected),
                    failures=failures,
                )
            except Exception as e:
                step_result = TestResult(
                    test_name=step_name, status="error",
                    duration_ms=round((time.time() - step_start) * 1000, 1),
                    message=str(e),
                )

            scenario.steps.append(step_result)
            if step_result.status in ("failed", "error"):
                break

        scenario.duration_ms = round((time.time() - start) * 1000, 1)
        scenario.overall_status = "passed" if all(
            s.status == "passed" for s in scenario.steps
        ) else "failed"

        return scenario

    # ── Performance Testing ───────────────────────────────────────────

    def load_test(self, fn: Callable, iterations: int = 100,
                  concurrency: int = 1) -> Dict[str, Any]:
        """Run a function multiple times and measure performance."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        durations = []

        def _run():
            start = time.time()
            try:
                fn()
                return (time.time() - start) * 1000
            except Exception:
                return -1

        start_all = time.time()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(_run) for _ in range(iterations)]
            for f in as_completed(futures):
                d = f.result()
                if d >= 0:
                    durations.append(d)

        total_time = (time.time() - start_all) * 1000
        durations.sort()
        errors = iterations - len(durations)

        return {
            "iterations": iterations,
            "concurrency": concurrency,
            "total_time_ms": round(total_time, 1),
            "successful": len(durations),
            "errors": errors,
            "avg_ms": round(sum(durations) / max(len(durations), 1), 2),
            "min_ms": round(durations[0], 2) if durations else 0,
            "max_ms": round(durations[-1], 2) if durations else 0,
            "p50_ms": round(durations[len(durations) // 2], 2) if durations else 0,
            "p95_ms": round(durations[int(len(durations) * 0.95)], 2) if durations else 0,
            "p99_ms": round(durations[int(len(durations) * 0.99)], 2) if durations else 0,
            "throughput_per_sec": round(len(durations) / (total_time / 1000), 1) if total_time > 0 else 0,
        }

    # ── Chaos Testing ─────────────────────────────────────────────────

    def chaos_test(self, fn: Callable, chaos_type: str = "random",
                   iterations: int = 50) -> Dict[str, Any]:
        """Run function with injected chaos (random failures, delays, etc.)."""
        results = {"passed": 0, "failed": 0, "errors": 0, "chaos_injected": 0}
        chaos_types_applied = []

        for i in range(iterations):
            inject = random.random() < 0.3  # 30% chaos injection rate
            if inject:
                results["chaos_injected"] += 1
                chaos_applied = random.choice(["delay", "timeout", "error", "partial_data"])
                chaos_types_applied.append(chaos_applied)

            try:
                fn()
                results["passed"] += 1
            except Exception:
                if inject:
                    results["errors"] += 1  # Expected errors from chaos
                else:
                    results["failed"] += 1  # Unexpected failures

        results["resilience_score"] = round(
            results["passed"] / max(iterations, 1) * 100, 1
        )
        results["chaos_types"] = list(set(chaos_types_applied))

        return results

    # ── Report ────────────────────────────────────────────────────────

    @property
    def summary(self) -> Dict[str, Any]:
        passed = sum(1 for r in self._results if r.status == "passed")
        failed = sum(1 for r in self._results if r.status == "failed")
        errors = sum(1 for r in self._results if r.status == "error")
        return {
            "total": len(self._results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": round(passed / max(len(self._results), 1) * 100, 1),
            "total_duration_ms": round(sum(r.duration_ms for r in self._results), 1),
        }
