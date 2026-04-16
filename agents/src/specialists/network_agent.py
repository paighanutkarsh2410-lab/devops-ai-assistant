"""
Network Specialist Agent: Latency analysis, packet loss, DNS issues,
firewall rules, load balancer health.
"""
import logging
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class NetworkSpecialistAgent(BaseSpecialist):
    AGENT_TYPE = "network"
    DOMAINS = ["network", "api"]
    ACTIONS = ["diagnose", "investigate", "trace"]

    LATENCY_WARN_MS = 100
    LATENCY_CRITICAL_MS = 500
    PACKET_LOSS_WARN_PCT = 1.0

    def __init__(self):
        super().__init__("network-specialist")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")
        text = f"{incident.get('root_cause', '')} {incident.get('description', '')}".lower()

        self._analyze_latency(service, report)

        if any(k in text for k in ("dns", "resolve", "hostname")):
            self._check_dns(service, report)
        if any(k in text for k in ("timeout", "connection refused", "firewall")):
            self._check_firewall(service, report)
        if any(k in text for k in ("load balancer", "lb", "upstream", "502", "503")):
            self._check_load_balancer(service, report)

        self._check_packet_loss(service, report)

    def _analyze_latency(self, service: str, report: SpecialistReport):
        # Simulated inter-service latency measurements
        routes = [
            {"from": "api-gateway", "to": service, "latency_ms": 45, "jitter_ms": 8},
            {"from": service, "to": "postgres", "latency_ms": 12, "jitter_ms": 3},
            {"from": service, "to": "redis", "latency_ms": 3, "jitter_ms": 1},
            {"from": service, "to": "external-api", "latency_ms": 380, "jitter_ms": 120},
        ]

        for route in routes:
            if route["latency_ms"] > self.LATENCY_CRITICAL_MS:
                sev = "critical"
            elif route["latency_ms"] > self.LATENCY_WARN_MS:
                sev = "high"
            else:
                continue

            report.findings.append(Finding(
                category="latency",
                severity=sev,
                title=f"High latency: {route['from']} → {route['to']} ({route['latency_ms']}ms)",
                description=f"Latency {route['latency_ms']}ms with {route['jitter_ms']}ms jitter",
                evidence=[
                    f"Measured latency: {route['latency_ms']}ms (threshold: {self.LATENCY_WARN_MS}ms)",
                    f"Jitter: {route['jitter_ms']}ms",
                ],
                recommendation=f"Investigate network path between {route['from']} and {route['to']}; check for congestion",
                confidence=85,
            ))

        report.metrics_analyzed["routes"] = routes

    def _check_dns(self, service: str, report: SpecialistReport):
        dns_results = [
            {"hostname": f"{service}.internal", "resolved": True, "time_ms": 5},
            {"hostname": "external-api.example.com", "resolved": True, "time_ms": 85},
        ]

        for dns in dns_results:
            if not dns["resolved"]:
                report.findings.append(Finding(
                    category="dns", severity="critical",
                    title=f"DNS resolution failed for {dns['hostname']}",
                    description="Unable to resolve hostname",
                    recommendation="Check DNS configuration and nameserver health",
                    confidence=95,
                ))
            elif dns["time_ms"] > 50:
                report.findings.append(Finding(
                    category="dns", severity="medium",
                    title=f"Slow DNS resolution for {dns['hostname']} ({dns['time_ms']}ms)",
                    description=f"DNS lookup took {dns['time_ms']}ms",
                    recommendation="Consider local DNS cache or reducing TTL",
                    confidence=75,
                ))

        report.metrics_analyzed["dns"] = dns_results

    def _check_firewall(self, service: str, report: SpecialistReport):
        blocked = [
            {"source": "10.0.1.0/24", "dest_port": 5432, "protocol": "tcp", "blocked_count": 150},
        ]

        for rule in blocked:
            if rule["blocked_count"] > 100:
                report.findings.append(Finding(
                    category="firewall", severity="high",
                    title=f"Excessive firewall blocks on port {rule['dest_port']}",
                    description=f"{rule['blocked_count']} blocked connections from {rule['source']}",
                    evidence=[f"Blocked: {rule['blocked_count']} packets from {rule['source']} to port {rule['dest_port']}"],
                    recommendation="Review firewall rules; verify legitimate traffic isn't being blocked",
                    confidence=80,
                ))

    def _check_load_balancer(self, service: str, report: SpecialistReport):
        lb = {
            "healthy_backends": 3,
            "unhealthy_backends": 1,
            "active_connections": 450,
            "requests_per_sec": 1200,
            "5xx_rate": 2.5,
        }

        if lb["unhealthy_backends"] > 0:
            report.findings.append(Finding(
                category="load_balancer", severity="high",
                title=f"{lb['unhealthy_backends']} unhealthy backend(s)",
                description=f"Load balancer sees {lb['unhealthy_backends']} unhealthy out of {lb['healthy_backends'] + lb['unhealthy_backends']} total backends",
                recommendation="Investigate unhealthy backends; check health check configuration",
                confidence=90,
            ))

        if lb["5xx_rate"] > 1.0:
            report.findings.append(Finding(
                category="load_balancer", severity="high",
                title=f"High 5xx rate at load balancer ({lb['5xx_rate']}%)",
                description=f"Error rate: {lb['5xx_rate']}% at {lb['requests_per_sec']} req/s",
                recommendation="Check backend logs; consider circuit breaker or traffic shaping",
                confidence=85,
            ))

        report.metrics_analyzed["load_balancer"] = lb

    def _check_packet_loss(self, service: str, report: SpecialistReport):
        loss_pct = 0.3  # Simulated
        if loss_pct > self.PACKET_LOSS_WARN_PCT:
            report.findings.append(Finding(
                category="packet_loss", severity="high",
                title=f"Packet loss detected ({loss_pct}%)",
                description=f"Network packet loss at {loss_pct}%",
                recommendation="Check network interface errors and switch port statistics",
                confidence=80,
            ))
        report.metrics_analyzed["packet_loss_pct"] = loss_pct
