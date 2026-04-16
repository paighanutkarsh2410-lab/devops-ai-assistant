"""
Performance Specialist Agent: Profiling, bottleneck identification,
code optimization suggestions, architecture recommendations.
"""
import logging
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class PerformanceSpecialistAgent(BaseSpecialist):
    AGENT_TYPE = "performance"
    DOMAINS = ["performance"]
    ACTIONS = ["diagnose", "profile", "optimize"]

    def __init__(self):
        super().__init__("performance-specialist")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")
        self._profile_service(service, report)
        self._identify_bottlenecks(service, report)
        self._check_resource_saturation(service, report)
        self._architecture_recommendations(service, context, report)

    def _profile_service(self, service: str, report: SpecialistReport):
        profile = {
            "cpu_breakdown": {
                "application": 45, "gc": 12, "io_wait": 25,
                "kernel": 8, "idle": 10,
            },
            "hot_functions": [
                {"name": "serialize_response", "cpu_pct": 18, "calls_per_sec": 5000},
                {"name": "query_database", "cpu_pct": 15, "calls_per_sec": 2000},
                {"name": "validate_token", "cpu_pct": 8, "calls_per_sec": 3000},
            ],
            "thread_states": {
                "runnable": 8, "waiting": 25, "blocked": 5, "timed_waiting": 12,
            },
        }

        # Check for IO bottleneck
        if profile["cpu_breakdown"]["io_wait"] > 20:
            report.findings.append(Finding(
                category="io_bottleneck", severity="high",
                title=f"High I/O wait ({profile['cpu_breakdown']['io_wait']}%)",
                description="CPU spending significant time waiting for I/O operations",
                evidence=[
                    f"I/O wait: {profile['cpu_breakdown']['io_wait']}%",
                    f"Top I/O function: {profile['hot_functions'][1]['name']}",
                ],
                recommendation="Optimize database queries, add caching, or use async I/O",
                confidence=85,
            ))

        # Check for blocked threads
        if profile["thread_states"]["blocked"] > 3:
            report.findings.append(Finding(
                category="thread_contention", severity="medium",
                title=f"{profile['thread_states']['blocked']} blocked threads",
                description="Thread contention detected",
                recommendation="Review synchronized blocks; consider lock-free data structures",
                confidence=75,
            ))

        # Hot function analysis
        for fn in profile["hot_functions"]:
            if fn["cpu_pct"] > 15:
                report.findings.append(Finding(
                    category="hot_path", severity="medium",
                    title=f"Hot function: {fn['name']} ({fn['cpu_pct']}% CPU)",
                    description=f"Called {fn['calls_per_sec']} times/sec, consuming {fn['cpu_pct']}% CPU",
                    recommendation=f"Optimize {fn['name']}; consider caching results or reducing call frequency",
                    confidence=70,
                ))

        report.metrics_analyzed["profile"] = profile

    def _identify_bottlenecks(self, service: str, report: SpecialistReport):
        bottlenecks = [
            {"component": "database", "impact": "high",
             "symptom": "Query response time 3x above baseline",
             "root_cause": "Missing index on frequently queried column"},
            {"component": "serialization", "impact": "medium",
             "symptom": "JSON serialization taking 18% CPU",
             "root_cause": "Large payloads with nested objects"},
        ]

        for b in bottlenecks:
            report.findings.append(Finding(
                category="bottleneck", severity=b["impact"],
                title=f"Bottleneck: {b['component']} — {b['symptom']}",
                description=f"Root cause: {b['root_cause']}",
                recommendation=f"Address {b['component']} bottleneck: {b['root_cause']}",
                confidence=78,
            ))

        report.metrics_analyzed["bottlenecks"] = bottlenecks

    def _check_resource_saturation(self, service: str, report: SpecialistReport):
        resources = {
            "cpu_pct": 78, "memory_pct": 72, "disk_io_pct": 45,
            "network_bandwidth_pct": 30, "file_descriptors_pct": 15,
            "connection_pool_pct": 85,
        }

        thresholds = {
            "cpu_pct": (70, 90), "memory_pct": (75, 90),
            "disk_io_pct": (60, 85), "network_bandwidth_pct": (60, 85),
            "file_descriptors_pct": (70, 90), "connection_pool_pct": (75, 90),
        }

        for name, value in resources.items():
            warn, crit = thresholds.get(name, (70, 90))
            if value > crit:
                sev = "critical"
            elif value > warn:
                sev = "high"
            else:
                continue

            label = name.replace("_pct", "").replace("_", " ").title()
            report.findings.append(Finding(
                category="saturation", severity=sev,
                title=f"{label} saturation: {value}%",
                description=f"Resource nearing capacity (warn: {warn}%, critical: {crit}%)",
                recommendation=f"Scale up {label.lower()} or optimize usage",
                confidence=85,
            ))

        report.metrics_analyzed["resource_saturation"] = resources

    def _architecture_recommendations(self, service: str, context: dict, report: SpecialistReport):
        # Based on findings, suggest architectural changes
        findings_categories = [f.category for f in report.findings]

        if "io_bottleneck" in findings_categories and "bottleneck" in findings_categories:
            report.recommendations.append(
                "Consider CQRS pattern: separate read/write paths to reduce database load"
            )
        if "hot_path" in findings_categories:
            report.recommendations.append(
                "Add response caching (Redis) for frequently accessed, rarely changing data"
            )
        if "saturation" in findings_categories:
            report.recommendations.append(
                "Implement horizontal auto-scaling based on CPU/memory thresholds"
            )
        if "thread_contention" in findings_categories:
            report.recommendations.append(
                "Migrate to async/event-driven architecture to reduce thread contention"
            )
