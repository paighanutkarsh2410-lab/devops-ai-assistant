"""
Security Monitoring & Alerting: Real-time threat detection, WAF simulation,
and security event correlation for SentryAI.
"""
import logging
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    timestamp: str
    event_type: str  # auth_failure, suspicious_request, rate_limit, intrusion, data_exfil, config_change
    severity: str    # critical, high, medium, low, info
    source_ip: str
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    correlated_events: List[str] = field(default_factory=list)


@dataclass
class ThreatIndicator:
    indicator: str          # IP, pattern, user agent, etc.
    indicator_type: str     # ip, pattern, user_agent, geo
    threat_level: str       # critical, high, medium, low
    first_seen: str = ""
    last_seen: str = ""
    hit_count: int = 0
    blocked: bool = False


@dataclass
class WAFRule:
    rule_id: str
    name: str
    pattern: str
    action: str = "block"   # block, log, challenge
    enabled: bool = True
    hits: int = 0
    last_triggered: str = ""


class SecurityMonitor:
    """
    Real-time security monitoring with threat detection, WAF, and alerting.
    """

    def __init__(self):
        self._events: deque = deque(maxlen=10000)
        self._threats: Dict[str, ThreatIndicator] = {}
        self._waf_rules: List[WAFRule] = []
        self._blocked_ips: set = set()
        self._lock = threading.Lock()
        self._alert_callbacks: List = []
        self._init_waf_rules()
        self._seed_demo_data()

    def _init_waf_rules(self):
        """Initialize WAF rules for common attack patterns."""
        self._waf_rules = [
            WAFRule("WAF-001", "SQL Injection", r"(?i)(union\s+select|drop\s+table|;.*--|'.*or.*'.*=)", hits=23),
            WAFRule("WAF-002", "XSS Attack", r"(?i)(<script|javascript:|on\w+\s*=)", hits=15),
            WAFRule("WAF-003", "Path Traversal", r"\.\./|\.\.\\|%2e%2e", hits=8),
            WAFRule("WAF-004", "Command Injection", r"(?i)(;|\||&&)\s*(rm|cat|wget|curl|nc|bash)", hits=5),
            WAFRule("WAF-005", "SSRF Attempt", r"(?i)(localhost|127\.0\.0\.1|169\.254\.\d+\.\d+|0\.0\.0\.0)", hits=3),
            WAFRule("WAF-006", "Bot Detection", r"(?i)(sqlmap|nikto|nmap|masscan|dirbuster)", hits=12),
            WAFRule("WAF-007", "API Abuse", r"(?i)/api/.*\.(php|asp|jsp|cgi)", hits=7),
            WAFRule("WAF-008", "Credential Stuffing", r"(?i)(admin|root|test).*password", action="challenge", hits=18),
        ]

    def _seed_demo_data(self):
        """Seed with realistic demo security events."""
        now = datetime.now(timezone.utc)
        demo_events = [
            ("auth_failure", "high", "203.0.113.42", {"user": "admin", "attempts": 12, "endpoint": "/auth/login"}),
            ("suspicious_request", "medium", "198.51.100.15", {"path": "/api/../../../etc/passwd", "method": "GET"}),
            ("rate_limit", "low", "192.0.2.88", {"requests_per_min": 450, "limit": 100, "endpoint": "/api/incidents"}),
            ("intrusion", "critical", "203.0.113.42", {"pattern": "SQL injection in search param", "payload": "' OR 1=1--", "blocked": True}),
            ("config_change", "medium", "10.0.0.5", {"change": "CORS origins modified", "user": "devops-admin"}),
            ("data_exfil", "high", "198.51.100.15", {"data_volume": "2.4GB", "endpoint": "/api/reports/export", "duration": "3min"}),
            ("auth_failure", "medium", "192.0.2.200", {"user": "service-account", "attempts": 3, "endpoint": "/auth/login"}),
            ("suspicious_request", "high", "203.0.113.99", {"path": "/api/users?role=admin", "method": "GET", "user_agent": "sqlmap/1.5"}),
        ]

        for i, (etype, sev, ip, details) in enumerate(demo_events):
            ts = (now - timedelta(minutes=len(demo_events) - i)).isoformat()
            self._events.append(SecurityEvent(
                timestamp=ts, event_type=etype, severity=sev,
                source_ip=ip, details=details,
                blocked=details.get("blocked", sev in ("critical", "high")),
            ))

        # Seed threat indicators
        self._threats = {
            "203.0.113.42": ThreatIndicator("203.0.113.42", "ip", "critical",
                first_seen=(now - timedelta(hours=2)).isoformat(), last_seen=now.isoformat(), hit_count=15, blocked=True),
            "198.51.100.15": ThreatIndicator("198.51.100.15", "ip", "high",
                first_seen=(now - timedelta(hours=1)).isoformat(), last_seen=now.isoformat(), hit_count=8, blocked=True),
            "sqlmap/*": ThreatIndicator("sqlmap/*", "user_agent", "critical",
                first_seen=(now - timedelta(minutes=30)).isoformat(), last_seen=now.isoformat(), hit_count=5, blocked=True),
        }
        self._blocked_ips = {"203.0.113.42", "198.51.100.15"}

    def record_event(self, event_type: str, severity: str, source_ip: str,
                     details: Dict[str, Any] = None) -> SecurityEvent:
        """Record a security event and evaluate threats."""
        event = SecurityEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type, severity=severity,
            source_ip=source_ip, details=details or {},
        )

        # Auto-block on critical events
        if severity == "critical":
            event.blocked = True
            self._blocked_ips.add(source_ip)

        # Update threat indicators
        self._update_threat(source_ip, severity)

        with self._lock:
            self._events.append(event)

        # Check WAF rules
        self._evaluate_waf(event)

        return event

    def _update_threat(self, source_ip: str, severity: str):
        """Update or create threat indicator for an IP."""
        now = datetime.now(timezone.utc).isoformat()
        if source_ip in self._threats:
            t = self._threats[source_ip]
            t.hit_count += 1
            t.last_seen = now
            if severity == "critical" and t.threat_level != "critical":
                t.threat_level = "critical"
        elif severity in ("critical", "high"):
            self._threats[source_ip] = ThreatIndicator(
                indicator=source_ip, indicator_type="ip",
                threat_level=severity, first_seen=now, last_seen=now, hit_count=1,
            )

    def _evaluate_waf(self, event: SecurityEvent):
        """Check event against WAF rules."""
        request_data = json.dumps(event.details) if event.details else ""
        for rule in self._waf_rules:
            if rule.enabled and re.search(rule.pattern, request_data):
                rule.hits += 1
                rule.last_triggered = event.timestamp
                if rule.action == "block":
                    event.blocked = True
                    self._blocked_ips.add(event.source_ip)

    def check_request(self, path: str, method: str, source_ip: str,
                      headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Check an incoming request against security rules."""
        if source_ip in self._blocked_ips:
            return {"allowed": False, "reason": "IP blocked", "rule": "blocklist"}

        full_request = f"{method} {path} {json.dumps(headers or {})}"
        for rule in self._waf_rules:
            if rule.enabled and re.search(rule.pattern, full_request):
                rule.hits += 1
                rule.last_triggered = datetime.now(timezone.utc).isoformat()
                if rule.action == "block":
                    return {"allowed": False, "reason": rule.name, "rule": rule.rule_id}
                elif rule.action == "challenge":
                    return {"allowed": True, "challenge": True, "reason": rule.name, "rule": rule.rule_id}

        return {"allowed": True}

    def get_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        now = datetime.now(timezone.utc)
        events = list(self._events)
        recent = [e for e in events if (now - datetime.fromisoformat(e.timestamp)).total_seconds() < 3600]

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        type_counts: Dict[str, int] = {}
        blocked_count = 0

        for e in recent:
            severity_counts[e.severity] = severity_counts.get(e.severity, 0) + 1
            type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1
            if e.blocked:
                blocked_count += 1

        return {
            "summary": {
                "total_events_1h": len(recent),
                "total_events_all": len(events),
                "blocked_requests": blocked_count,
                "blocked_ips": len(self._blocked_ips),
                "active_threats": len([t for t in self._threats.values() if t.threat_level in ("critical", "high")]),
            },
            "severity_breakdown": severity_counts,
            "event_types": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
            "recent_events": [
                {
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "source_ip": e.source_ip,
                    "blocked": e.blocked,
                    "details": e.details,
                }
                for e in list(reversed(events))[:20]
            ],
            "threats": [
                {
                    "indicator": t.indicator,
                    "type": t.indicator_type,
                    "threat_level": t.threat_level,
                    "hit_count": t.hit_count,
                    "first_seen": t.first_seen,
                    "last_seen": t.last_seen,
                    "blocked": t.blocked,
                }
                for t in sorted(self._threats.values(), key=lambda t: -t.hit_count)
            ],
            "waf_rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "action": r.action,
                    "enabled": r.enabled,
                    "hits": r.hits,
                    "last_triggered": r.last_triggered,
                }
                for r in self._waf_rules
            ],
        }

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_events": len(self._events),
            "blocked_ips": len(self._blocked_ips),
            "active_threats": len(self._threats),
            "waf_rules": len(self._waf_rules),
        }


# Need json for _evaluate_waf
import json
