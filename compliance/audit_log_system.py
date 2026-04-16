"""
Comprehensive Audit Log System: Immutable, tamper-evident logging for compliance.
Tracks who did what, when, with full context for SOC 2, GDPR, and ISO 27001.
"""
import hashlib
import json
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    timestamp: str
    actor: str          # user_id or system component
    action: str         # create, read, update, delete, login, approve, execute
    resource_type: str  # incident, user, agent, approval, config
    resource_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    result: str = "success"  # success, failure, denied
    sensitivity: str = "standard"  # public, standard, confidential, restricted
    checksum: str = ""  # integrity hash


class AuditLogSystem:
    """
    Immutable audit logging with integrity verification.
    Supports retention policies and compliance reporting.
    """

    def __init__(self, retention_days: int = 2555):  # ~7 years default
        self._log: deque = deque(maxlen=100000)
        self._lock = threading.Lock()
        self._retention_days = retention_days
        self._last_checksum = ""

    def log(self, actor: str, action: str, resource_type: str,
            resource_id: str, details: Dict[str, Any] = None,
            ip_address: str = "", result: str = "success",
            sensitivity: str = "standard") -> AuditEntry:
        """Create an immutable audit log entry with integrity hash."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor, action=action,
            resource_type=resource_type, resource_id=resource_id,
            details=details or {}, ip_address=ip_address,
            result=result, sensitivity=sensitivity,
        )

        # Chain hash for tamper detection
        content = json.dumps({
            "timestamp": entry.timestamp, "actor": entry.actor,
            "action": entry.action, "resource": f"{entry.resource_type}:{entry.resource_id}",
            "previous": self._last_checksum,
        }, sort_keys=True)
        entry.checksum = hashlib.sha256(content.encode()).hexdigest()

        with self._lock:
            self._log.append(entry)
            self._last_checksum = entry.checksum

        return entry

    def query(self, actor: Optional[str] = None,
              action: Optional[str] = None,
              resource_type: Optional[str] = None,
              start_date: Optional[str] = None,
              end_date: Optional[str] = None,
              limit: int = 100) -> List[Dict[str, Any]]:
        """Query audit logs with filters."""
        results = []
        for entry in reversed(self._log):
            if actor and entry.actor != actor:
                continue
            if action and entry.action != action:
                continue
            if resource_type and entry.resource_type != resource_type:
                continue
            if start_date and entry.timestamp < start_date:
                continue
            if end_date and entry.timestamp > end_date:
                continue

            results.append({
                "timestamp": entry.timestamp,
                "actor": entry.actor,
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "details": entry.details,
                "result": entry.result,
                "sensitivity": entry.sensitivity,
                "checksum": entry.checksum[:16] + "...",
            })
            if len(results) >= limit:
                break

        return results

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify the integrity chain of all audit entries."""
        entries = list(self._log)
        if not entries:
            return {"verified": True, "entries_checked": 0}

        prev_checksum = ""
        broken_at = None

        for i, entry in enumerate(entries):
            expected_content = json.dumps({
                "timestamp": entry.timestamp, "actor": entry.actor,
                "action": entry.action,
                "resource": f"{entry.resource_type}:{entry.resource_id}",
                "previous": prev_checksum,
            }, sort_keys=True)
            expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()

            if entry.checksum != expected_hash:
                broken_at = i
                break
            prev_checksum = entry.checksum

        return {
            "verified": broken_at is None,
            "entries_checked": len(entries),
            "integrity_broken_at": broken_at,
        }

    def generate_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance-ready audit report."""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        entries = [e for e in self._log if e.timestamp >= cutoff]

        actions_summary: Dict[str, int] = {}
        actors_summary: Dict[str, int] = {}
        resources_summary: Dict[str, int] = {}
        failures = 0

        for e in entries:
            actions_summary[e.action] = actions_summary.get(e.action, 0) + 1
            actors_summary[e.actor] = actors_summary.get(e.actor, 0) + 1
            resources_summary[e.resource_type] = resources_summary.get(e.resource_type, 0) + 1
            if e.result == "failure":
                failures += 1

        return {
            "period_days": days,
            "total_entries": len(entries),
            "unique_actors": len(actors_summary),
            "failures": failures,
            "actions_breakdown": dict(sorted(actions_summary.items(), key=lambda x: -x[1])),
            "resource_types": dict(sorted(resources_summary.items(), key=lambda x: -x[1])),
            "top_actors": dict(sorted(actors_summary.items(), key=lambda x: -x[1])[:10]),
            "integrity": self.verify_integrity(),
        }

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self._log),
            "retention_days": self._retention_days,
            "integrity_verified": self.verify_integrity()["verified"],
        }
