"""Escalation service — auto-escalate incidents based on policies."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.incident import Incident
from models.escalation_policy import EscalationPolicy, EscalationRecord, OnCallRotation
import logging

logger = logging.getLogger(__name__)


class EscalationService:
    """Manages incident escalations based on configurable policies."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def start_escalation(self, incident_id: str) -> dict:
        """Start escalation for an incident based on matching policy."""
        incident = self.db.query(Incident).filter(
            Incident.id == incident_id, Incident.user_id == self.user_id
        ).first()
        if not incident:
            return {"error": "Incident not found"}

        # Find matching policy
        policy = self._find_policy(incident)
        if not policy:
            return {"error": "No matching escalation policy", "incident_id": str(incident_id)}

        levels = policy.levels or []
        if not levels:
            return {"error": "Policy has no escalation levels"}

        first_level = levels[0]
        wait_minutes = first_level.get("wait_minutes", 15)

        record = EscalationRecord(
            user_id=self.user_id,
            incident_id=incident.id,
            policy_id=policy.id,
            current_level=1,
            status="active",
            notified_contacts=first_level.get("notify", []),
            escalation_history=[{
                "level": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "contacts": first_level.get("notify", []),
                "methods": first_level.get("method", ["slack"]),
            }],
            next_escalation_at=datetime.utcnow() + timedelta(minutes=wait_minutes),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return self._serialize_record(record)

    def check_escalation_needed(self, incident_id: str) -> dict:
        """Check if an incident needs escalation to next level."""
        record = self.db.query(EscalationRecord).filter(
            EscalationRecord.incident_id == incident_id,
            EscalationRecord.user_id == self.user_id,
            EscalationRecord.status == "active",
        ).first()

        if not record:
            return {"needs_escalation": False, "reason": "No active escalation"}

        if record.next_escalation_at and datetime.utcnow() >= record.next_escalation_at:
            return {"needs_escalation": True, "current_level": record.current_level, "record_id": str(record.id)}

        remaining = (record.next_escalation_at - datetime.utcnow()).total_seconds() if record.next_escalation_at else 0
        return {
            "needs_escalation": False,
            "current_level": record.current_level,
            "seconds_until_next": max(0, int(remaining)),
        }

    def escalate_to_next_level(self, incident_id: str) -> dict:
        """Escalate to the next level."""
        record = self.db.query(EscalationRecord).filter(
            EscalationRecord.incident_id == incident_id,
            EscalationRecord.user_id == self.user_id,
            EscalationRecord.status == "active",
        ).first()

        if not record:
            return {"error": "No active escalation for this incident"}

        policy = self.db.query(EscalationPolicy).filter(EscalationPolicy.id == record.policy_id).first()
        if not policy:
            return {"error": "Policy not found"}

        levels = policy.levels or []
        next_level_idx = record.current_level  # 0-indexed: level 1 = index 0, so next = current_level

        if next_level_idx >= len(levels):
            record.status = "max_reached"
            self.db.commit()
            return {"error": "Maximum escalation level reached", "current_level": record.current_level}

        next_level = levels[next_level_idx]
        wait_minutes = next_level.get("wait_minutes", 30)

        history = record.escalation_history or []
        history.append({
            "level": next_level_idx + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "contacts": next_level.get("notify", []),
            "methods": next_level.get("method", ["slack", "email"]),
        })

        record.current_level = next_level_idx + 1
        record.notified_contacts = next_level.get("notify", [])
        record.escalation_history = history
        record.next_escalation_at = datetime.utcnow() + timedelta(minutes=wait_minutes)
        self.db.commit()

        return self._serialize_record(record)

    def acknowledge_escalation(self, incident_id: str) -> dict:
        """Acknowledge an escalation — stops further escalation."""
        record = self.db.query(EscalationRecord).filter(
            EscalationRecord.incident_id == incident_id,
            EscalationRecord.user_id == self.user_id,
            EscalationRecord.status == "active",
        ).first()

        if not record:
            return {"error": "No active escalation"}

        record.status = "acknowledged"
        record.acknowledged_at = datetime.utcnow()
        record.next_escalation_at = None
        self.db.commit()

        return self._serialize_record(record)

    def get_on_call(self) -> dict:
        """Get current on-call personnel."""
        schedules = self.db.query(OnCallRotation).filter(
            OnCallRotation.user_id == self.user_id
        ).all()

        result = []
        for sched in schedules:
            participants = sched.participants or []
            if not participants:
                continue
            current = participants[sched.current_index % len(participants)]
            result.append({
                "schedule_name": sched.name,
                "rotation_type": sched.rotation_type,
                "current_on_call": current,
                "total_participants": len(participants),
                "overrides": sched.overrides or [],
            })

        return {"on_call": result}

    def get_escalation_analytics(self) -> dict:
        """Analytics on escalation patterns."""
        records = self.db.query(EscalationRecord).filter(
            EscalationRecord.user_id == self.user_id
        ).all()

        total = len(records)
        acknowledged = sum(1 for r in records if r.status == "acknowledged")
        max_reached = sum(1 for r in records if r.status == "max_reached")

        ack_times = []
        for r in records:
            if r.acknowledged_at and r.started_at:
                delta = (r.acknowledged_at - r.started_at).total_seconds() / 60
                ack_times.append(delta)

        level_counts: dict[int, int] = {}
        for r in records:
            level_counts[r.current_level] = level_counts.get(r.current_level, 0) + 1

        return {
            "total_escalations": total,
            "acknowledged": acknowledged,
            "max_level_reached": max_reached,
            "avg_ack_time_minutes": round(sum(ack_times) / len(ack_times), 1) if ack_times else 0,
            "level_distribution": level_counts,
            "acknowledgment_rate": round(acknowledged / max(total, 1) * 100, 1),
        }

    def _find_policy(self, incident: Incident) -> EscalationPolicy | None:
        """Find the best matching policy for an incident."""
        policies = self.db.query(EscalationPolicy).filter(
            EscalationPolicy.user_id == self.user_id,
            EscalationPolicy.enabled == True,
        ).all()

        for policy in policies:
            # Match by service
            if policy.service_name and policy.service_name != incident.service_name:
                continue
            # Match by severity
            sev_levels = policy.severity_levels or []
            if sev_levels and incident.severity not in sev_levels:
                continue
            return policy

        return policies[0] if policies else None

    def _serialize_record(self, r: EscalationRecord) -> dict:
        return {
            "id": str(r.id),
            "incident_id": str(r.incident_id),
            "policy_id": str(r.policy_id) if r.policy_id else None,
            "current_level": r.current_level,
            "status": r.status,
            "notified_contacts": r.notified_contacts,
            "escalation_history": r.escalation_history,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
            "next_escalation_at": r.next_escalation_at.isoformat() if r.next_escalation_at else None,
        }
