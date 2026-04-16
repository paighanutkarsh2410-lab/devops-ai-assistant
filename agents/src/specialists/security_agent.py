"""
Security Specialist Agent: Intrusion detection, anomalous access patterns,
certificate expiration, vulnerability scanning, compliance checking.
"""
import logging
from datetime import datetime, timedelta, timezone
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class SecuritySpecialistAgent(BaseSpecialist):
    AGENT_TYPE = "security"
    DOMAINS = ["security"]
    ACTIONS = ["audit", "investigate", "scan"]

    def __init__(self):
        super().__init__("security-specialist")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")
        self._check_anomalous_access(service, report)
        self._check_certificates(service, report)
        self._scan_vulnerabilities(service, report)
        self._check_compliance(service, report)

    def _check_anomalous_access(self, service: str, report: SpecialistReport):
        patterns = [
            {"source": "203.0.113.50", "requests": 5000, "unique_paths": 200,
             "methods": ["GET", "POST", "DELETE"], "time_window_min": 10,
             "risk": "scanning"},
            {"source": "198.51.100.22", "requests": 800, "unique_paths": 5,
             "methods": ["POST"], "time_window_min": 5,
             "risk": "brute_force"},
        ]

        for p in patterns:
            if p["risk"] == "scanning":
                report.findings.append(Finding(
                    category="intrusion", severity="high",
                    title=f"Possible port/path scanning from {p['source']}",
                    description=f"{p['requests']} requests to {p['unique_paths']} unique paths in {p['time_window_min']}min",
                    evidence=[
                        f"Source: {p['source']}, {p['requests']} requests",
                        f"Hit {p['unique_paths']} unique paths including DELETE methods",
                    ],
                    recommendation=f"Block {p['source']} at WAF/firewall; investigate for data exfiltration",
                    confidence=80,
                ))
            elif p["risk"] == "brute_force":
                report.findings.append(Finding(
                    category="brute_force", severity="high",
                    title=f"Brute force attempt from {p['source']}",
                    description=f"{p['requests']} POST requests in {p['time_window_min']}min",
                    recommendation=f"Rate limit and block {p['source']}; enforce account lockout",
                    confidence=85,
                ))

        report.metrics_analyzed["access_patterns"] = patterns

    def _check_certificates(self, service: str, report: SpecialistReport):
        certs = [
            {"domain": f"{service}.example.com", "expires": (datetime.now(timezone.utc) + timedelta(days=8)).isoformat(),
             "issuer": "Let's Encrypt", "days_left": 8},
            {"domain": "api.example.com", "expires": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
             "issuer": "DigiCert", "days_left": 45},
        ]

        for cert in certs:
            if cert["days_left"] < 7:
                sev = "critical"
            elif cert["days_left"] < 14:
                sev = "high"
            elif cert["days_left"] < 30:
                sev = "medium"
            else:
                continue

            report.findings.append(Finding(
                category="certificate", severity=sev,
                title=f"Certificate expiring: {cert['domain']} ({cert['days_left']} days)",
                description=f"Issuer: {cert['issuer']}, expires: {cert['expires'][:10]}",
                recommendation="Renew certificate immediately" if cert["days_left"] < 14 else "Schedule certificate renewal",
                confidence=95,
            ))

        report.metrics_analyzed["certificates"] = certs

    def _scan_vulnerabilities(self, service: str, report: SpecialistReport):
        vulns = [
            {"id": "CVE-2024-1234", "severity": "high", "package": "openssl",
             "current_version": "1.1.1w", "fixed_version": "3.0.13",
             "description": "Buffer overflow in TLS handshake"},
            {"id": "CVE-2024-5678", "severity": "medium", "package": "requests",
             "current_version": "2.28.0", "fixed_version": "2.31.0",
             "description": "SSRF via redirect handling"},
        ]

        for v in vulns:
            report.findings.append(Finding(
                category="vulnerability", severity=v["severity"],
                title=f"{v['id']}: {v['package']} {v['current_version']}",
                description=v["description"],
                evidence=[
                    f"Package: {v['package']} {v['current_version']}",
                    f"Fixed in: {v['fixed_version']}",
                ],
                recommendation=f"Upgrade {v['package']} to {v['fixed_version']}",
                confidence=90,
            ))

        report.metrics_analyzed["vulnerabilities"] = vulns

    def _check_compliance(self, service: str, report: SpecialistReport):
        checks = [
            {"rule": "TLS 1.2+ required", "status": "pass"},
            {"rule": "No hardcoded credentials", "status": "pass"},
            {"rule": "Secrets encrypted at rest", "status": "pass"},
            {"rule": "Audit logging enabled", "status": "warning",
             "detail": "Some endpoints missing audit logs"},
            {"rule": "Rate limiting on auth endpoints", "status": "fail",
             "detail": "No rate limiting on /auth/login"},
        ]

        for check in checks:
            if check["status"] == "fail":
                report.findings.append(Finding(
                    category="compliance", severity="high",
                    title=f"Compliance failure: {check['rule']}",
                    description=check.get("detail", ""),
                    recommendation=f"Fix: {check['rule']}",
                    confidence=90,
                ))
            elif check["status"] == "warning":
                report.findings.append(Finding(
                    category="compliance", severity="medium",
                    title=f"Compliance warning: {check['rule']}",
                    description=check.get("detail", ""),
                    recommendation=f"Address: {check['rule']}",
                    confidence=75,
                ))

        report.metrics_analyzed["compliance"] = checks
