"""
Cost Optimizer Agent: Resource right-sizing, unused resource detection,
reserved instance recommendations, cost anomaly detection.
"""
import logging
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class CostOptimizerAgent(BaseSpecialist):
    AGENT_TYPE = "cost"
    DOMAINS = ["cost"]
    ACTIONS = ["optimize", "analyze", "recommend"]

    def __init__(self):
        super().__init__("cost-optimizer")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")
        self._detect_oversized_resources(service, report)
        self._find_unused_resources(service, report)
        self._recommend_reserved_instances(service, report)
        self._detect_cost_anomalies(service, report)

    def _detect_oversized_resources(self, service: str, report: SpecialistReport):
        resources = [
            {"name": f"{service}-main", "type": "compute", "size": "xlarge",
             "avg_cpu_pct": 15, "avg_mem_pct": 30, "recommended": "medium",
             "monthly_cost": 180, "savings": 90},
            {"name": f"{service}-worker", "type": "compute", "size": "large",
             "avg_cpu_pct": 8, "avg_mem_pct": 20, "recommended": "small",
             "monthly_cost": 90, "savings": 60},
        ]

        total_savings = 0
        for r in resources:
            if r["avg_cpu_pct"] < 30 and r["avg_mem_pct"] < 40:
                total_savings += r["savings"]
                report.findings.append(Finding(
                    category="oversized", severity="medium",
                    title=f"Oversized resource: {r['name']} ({r['size']} → {r['recommended']})",
                    description=f"CPU: {r['avg_cpu_pct']}%, Memory: {r['avg_mem_pct']}%. Save ${r['savings']}/mo",
                    evidence=[
                        f"Average CPU utilization: {r['avg_cpu_pct']}%",
                        f"Average memory utilization: {r['avg_mem_pct']}%",
                        f"Current size: {r['size']}, recommended: {r['recommended']}",
                    ],
                    recommendation=f"Downsize {r['name']} from {r['size']} to {r['recommended']} (save ${r['savings']}/mo)",
                    confidence=80,
                ))

        report.metrics_analyzed["rightsizing"] = resources
        report.metrics_analyzed["potential_savings"] = total_savings

    def _find_unused_resources(self, service: str, report: SpecialistReport):
        unused = [
            {"name": "staging-db-replica", "type": "database", "idle_days": 45,
             "monthly_cost": 120},
            {"name": "old-cache-cluster", "type": "cache", "idle_days": 30,
             "monthly_cost": 65},
        ]

        for r in unused:
            if r["idle_days"] > 14:
                report.findings.append(Finding(
                    category="unused_resource", severity="low",
                    title=f"Unused resource: {r['name']} (idle {r['idle_days']}d)",
                    description=f"Type: {r['type']}, costing ${r['monthly_cost']}/mo with no traffic",
                    recommendation=f"Terminate {r['name']} to save ${r['monthly_cost']}/mo",
                    confidence=85,
                ))

        report.metrics_analyzed["unused_resources"] = unused

    def _recommend_reserved_instances(self, service: str, report: SpecialistReport):
        candidates = [
            {"instance_type": "m5.xlarge", "count": 3, "usage_pct": 95,
             "on_demand_cost": 540, "reserved_cost": 340, "term": "1yr"},
        ]

        for c in candidates:
            if c["usage_pct"] > 80:
                savings = c["on_demand_cost"] - c["reserved_cost"]
                report.findings.append(Finding(
                    category="reserved_instance", severity="info",
                    title=f"RI opportunity: {c['count']}x {c['instance_type']}",
                    description=f"Steady {c['usage_pct']}% utilization. Save ${savings}/mo with {c['term']} commitment",
                    recommendation=f"Purchase {c['count']}x {c['instance_type']} {c['term']} reserved instances",
                    confidence=75,
                ))

        report.metrics_analyzed["ri_candidates"] = candidates

    def _detect_cost_anomalies(self, service: str, report: SpecialistReport):
        daily_costs = [
            {"date": "2026-04-01", "cost": 45}, {"date": "2026-04-02", "cost": 48},
            {"date": "2026-04-03", "cost": 46}, {"date": "2026-04-04", "cost": 120},
            {"date": "2026-04-05", "cost": 115}, {"date": "2026-04-06", "cost": 110},
        ]

        avg_normal = sum(d["cost"] for d in daily_costs[:3]) / 3
        recent = daily_costs[-1]["cost"]

        if recent > avg_normal * 1.5:
            spike_pct = ((recent - avg_normal) / avg_normal) * 100
            report.findings.append(Finding(
                category="cost_anomaly", severity="high",
                title=f"Cost spike detected: +{spike_pct:.0f}% above normal",
                description=f"Recent: ${recent}/day vs normal: ${avg_normal:.0f}/day",
                evidence=[
                    f"Normal average: ${avg_normal:.0f}/day",
                    f"Current: ${recent}/day (+{spike_pct:.0f}%)",
                ],
                recommendation="Investigate new resources or traffic spike causing increased costs",
                confidence=80,
            ))

        report.metrics_analyzed["daily_costs"] = daily_costs
