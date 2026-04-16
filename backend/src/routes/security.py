"""Security monitoring & alerting API endpoints."""
import sys
import os
from fastapi import APIRouter, Depends
from utils.auth import get_current_user

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "security"))

router = APIRouter(prefix="/security", tags=["security"])

_monitor = None


def _get_monitor():
    global _monitor
    if _monitor is None:
        from security_monitor import SecurityMonitor
        _monitor = SecurityMonitor()
    return _monitor


@router.get("/dashboard")
def security_dashboard(current_user=Depends(get_current_user)):
    """Get security monitoring dashboard data."""
    return _get_monitor().get_dashboard()


@router.get("/threats")
def get_threats(current_user=Depends(get_current_user)):
    """Get active threat indicators."""
    dashboard = _get_monitor().get_dashboard()
    return {"threats": dashboard["threats"], "blocked_ips": list(_get_monitor()._blocked_ips)}


@router.get("/waf/rules")
def get_waf_rules(current_user=Depends(get_current_user)):
    """Get WAF rules and stats."""
    dashboard = _get_monitor().get_dashboard()
    return {"rules": dashboard["waf_rules"]}


@router.post("/waf/rules/{rule_id}/toggle")
def toggle_waf_rule(rule_id: str, current_user=Depends(get_current_user)):
    """Enable/disable a WAF rule."""
    monitor = _get_monitor()
    for rule in monitor._waf_rules:
        if rule.rule_id == rule_id:
            rule.enabled = not rule.enabled
            return {"rule_id": rule_id, "enabled": rule.enabled}
    return {"error": "Rule not found"}


@router.get("/events")
def get_events(severity: str = None, event_type: str = None, limit: int = 50,
               current_user=Depends(get_current_user)):
    """Get security events with optional filters."""
    events = list(reversed(list(_get_monitor()._events)))
    if severity:
        events = [e for e in events if e.severity == severity]
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    return {
        "events": [
            {
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "severity": e.severity,
                "source_ip": e.source_ip,
                "blocked": e.blocked,
                "details": e.details,
            }
            for e in events[:limit]
        ]
    }
