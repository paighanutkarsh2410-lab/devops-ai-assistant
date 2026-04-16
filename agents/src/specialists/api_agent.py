"""
API Specialist Agent: Rate limiting, auth issues, timeout patterns,
response time analysis, circuit breaker state.
"""
import logging
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class APISpecialistAgent(BaseSpecialist):
    AGENT_TYPE = "api"
    DOMAINS = ["api", "performance"]
    ACTIONS = ["diagnose", "investigate", "analyze"]

    RESPONSE_WARN_MS = 500
    ERROR_RATE_WARN_PCT = 2.0

    def __init__(self):
        super().__init__("api-specialist")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")
        text = f"{incident.get('root_cause', '')} {incident.get('description', '')}".lower()

        self._analyze_response_times(service, report)
        self._check_error_rates(service, report)

        if any(k in text for k in ("rate limit", "429", "throttl")):
            self._check_rate_limits(service, report)
        if any(k in text for k in ("auth", "401", "403", "token")):
            self._check_auth_issues(service, report)
        if any(k in text for k in ("timeout", "504", "circuit")):
            self._check_circuit_breakers(service, report)

        self._identify_bottleneck_endpoints(service, report)

    def _analyze_response_times(self, service: str, report: SpecialistReport):
        endpoints = [
            {"path": "/api/incidents", "p50": 45, "p95": 180, "p99": 850, "rpm": 500},
            {"path": "/api/metrics", "p50": 120, "p95": 450, "p99": 2100, "rpm": 1200},
            {"path": "/api/auth/login", "p50": 80, "p95": 200, "p99": 500, "rpm": 300},
            {"path": "/api/reports/generate", "p50": 2500, "p95": 8000, "p99": 15000, "rpm": 20},
        ]

        for ep in endpoints:
            if ep["p95"] > self.RESPONSE_WARN_MS:
                report.findings.append(Finding(
                    category="response_time",
                    severity="high" if ep["p95"] > 2000 else "medium",
                    title=f"Slow endpoint: {ep['path']} (p95: {ep['p95']}ms)",
                    description=f"p50={ep['p50']}ms, p95={ep['p95']}ms, p99={ep['p99']}ms at {ep['rpm']} req/min",
                    evidence=[
                        f"p95 latency: {ep['p95']}ms exceeds {self.RESPONSE_WARN_MS}ms threshold",
                        f"p99 latency: {ep['p99']}ms ({ep['p99']/ep['p50']:.0f}x p50)",
                    ],
                    recommendation=f"Profile {ep['path']}; check DB queries, external calls, and payload size",
                    confidence=85,
                ))

        report.metrics_analyzed["endpoints"] = endpoints

    def _check_error_rates(self, service: str, report: SpecialistReport):
        errors = {
            "total_requests": 50000,
            "4xx_count": 1200, "5xx_count": 350,
            "4xx_rate": 2.4, "5xx_rate": 0.7,
            "top_errors": [
                {"code": 429, "count": 800, "path": "/api/metrics"},
                {"code": 500, "count": 200, "path": "/api/reports/generate"},
                {"code": 404, "count": 400, "path": "/api/unknown"},
            ],
        }

        if errors["5xx_rate"] > self.ERROR_RATE_WARN_PCT:
            report.findings.append(Finding(
                category="error_rate", severity="critical",
                title=f"High 5xx error rate ({errors['5xx_rate']}%)",
                description=f"{errors['5xx_count']} server errors out of {errors['total_requests']} requests",
                recommendation="Check application logs for stack traces; review recent deployments",
                confidence=90,
            ))

        for err in errors["top_errors"]:
            if err["code"] == 429 and err["count"] > 500:
                report.findings.append(Finding(
                    category="rate_limiting", severity="high",
                    title=f"Excessive 429s on {err['path']} ({err['count']} hits)",
                    description="Clients being rate limited heavily",
                    recommendation="Increase rate limits or optimize client retry behavior",
                    confidence=85,
                ))

        report.metrics_analyzed["error_rates"] = errors

    def _check_rate_limits(self, service: str, report: SpecialistReport):
        limits = {
            "global_limit": 10000, "current_rate": 8500,
            "per_client_limit": 200,
            "top_clients": [
                {"client": "mobile-app", "rate": 180, "limit": 200},
                {"client": "monitoring", "rate": 150, "limit": 200},
            ],
        }

        usage_pct = (limits["current_rate"] / limits["global_limit"]) * 100
        if usage_pct > 80:
            report.findings.append(Finding(
                category="rate_limit", severity="high" if usage_pct > 90 else "medium",
                title=f"Approaching global rate limit ({usage_pct:.0f}%)",
                description=f"Current: {limits['current_rate']}/{limits['global_limit']} req/min",
                recommendation="Scale API instances or implement request queuing",
                confidence=80,
            ))

        report.metrics_analyzed["rate_limits"] = limits

    def _check_auth_issues(self, service: str, report: SpecialistReport):
        auth = {
            "failed_logins_per_min": 45,
            "expired_tokens": 120,
            "invalid_tokens": 30,
            "avg_token_age_min": 25,
        }

        if auth["failed_logins_per_min"] > 30:
            report.findings.append(Finding(
                category="auth", severity="high",
                title=f"High login failure rate ({auth['failed_logins_per_min']}/min)",
                description="Possible brute force attempt or client misconfiguration",
                recommendation="Check for credential stuffing; verify client configurations",
                confidence=75,
            ))

        if auth["expired_tokens"] > 50:
            report.findings.append(Finding(
                category="auth", severity="medium",
                title=f"Many expired token rejections ({auth['expired_tokens']})",
                description="Clients using stale tokens",
                recommendation="Check token TTL configuration; implement proactive token refresh",
                confidence=70,
            ))

        report.metrics_analyzed["auth"] = auth

    def _check_circuit_breakers(self, service: str, report: SpecialistReport):
        breakers = [
            {"target": "payment-service", "state": "half-open", "failures": 15, "threshold": 10},
            {"target": "email-service", "state": "open", "failures": 50, "threshold": 10},
        ]

        for cb in breakers:
            if cb["state"] in ("open", "half-open"):
                report.findings.append(Finding(
                    category="circuit_breaker",
                    severity="critical" if cb["state"] == "open" else "high",
                    title=f"Circuit breaker {cb['state']} for {cb['target']}",
                    description=f"{cb['failures']} failures (threshold: {cb['threshold']})",
                    recommendation=f"Investigate {cb['target']} health; check for cascading failures",
                    confidence=90,
                ))

        report.metrics_analyzed["circuit_breakers"] = breakers

    def _identify_bottleneck_endpoints(self, service: str, report: SpecialistReport):
        # Weighted score: latency * traffic
        endpoints = report.metrics_analyzed.get("endpoints", [])
        for ep in endpoints:
            impact = ep["p95"] * ep["rpm"]
            if impact > 500000:
                report.recommendations.append(
                    f"High-impact endpoint: {ep['path']} (p95={ep['p95']}ms x {ep['rpm']}rpm)"
                )
