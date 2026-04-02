"""Incident timeline generation service."""
from sqlalchemy.orm import Session
from models.incident import Incident
from models.alert import Alert
from models.metric import Metric
from models.log_entry import LogEntry
from models.deployment import Deployment
from datetime import timedelta
from typing import List


def generate_timeline(db: Session, incident_id: str, user_id) -> List[dict]:
    """
    Generate a chronological timeline of all events related to an incident.
    """
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == user_id
    ).first()

    if not incident:
        return []

    events = []
    detected = incident.detected_at
    window_start = detected - timedelta(minutes=30)
    window_end = incident.resolved_at or (detected + timedelta(hours=2))

    # 1. Incident detection
    events.append({
        "timestamp": detected.isoformat(),
        "event_type": "detection",
        "description": f"Incident detected: {incident.title}",
        "metadata": {"severity": incident.severity, "service": incident.service_name}
    })

    # 2. Related alerts
    alerts = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.triggered_at.between(window_start, window_end)
    ).order_by(Alert.triggered_at).all()

    for alert in alerts:
        events.append({
            "timestamp": alert.triggered_at.isoformat(),
            "event_type": "alert",
            "description": f"Alert: {alert.title} [{alert.severity}]",
            "metadata": {"alert_id": str(alert.id), "severity": alert.severity}
        })

    # 3. Metric anomalies (high values around incident time)
    if incident.service_name:
        metrics = db.query(Metric).filter(
            Metric.user_id == user_id,
            Metric.service_name == incident.service_name,
            Metric.timestamp.between(window_start, window_end)
        ).order_by(Metric.timestamp).all()

        # Find metric spikes
        for m in metrics:
            is_spike = (
                (m.metric_name == "cpu" and m.value > 80) or
                (m.metric_name == "memory" and m.value > 85) or
                (m.metric_name == "error_rate" and m.value > 5) or
                (m.metric_name == "response_time" and m.value > 500)
            )
            if is_spike:
                events.append({
                    "timestamp": m.timestamp.isoformat(),
                    "event_type": "metric_spike",
                    "description": f"{m.metric_name} spike: {m.value:.1f}{m.unit or ''} on {m.service_name}",
                    "metadata": {"metric": m.metric_name, "value": m.value}
                })

    # 4. Deployments around incident time
    deployments = db.query(Deployment).filter(
        Deployment.user_id == user_id,
        Deployment.deployed_at.between(window_start, window_end)
    ).order_by(Deployment.deployed_at).all()

    for dep in deployments:
        events.append({
            "timestamp": dep.deployed_at.isoformat(),
            "event_type": "deployment",
            "description": f"Deployment: {dep.service_name} v{dep.version} by {dep.deployed_by or 'unknown'}",
            "metadata": {"service": dep.service_name, "version": dep.version}
        })

    # 5. Error logs around incident time
    if incident.service_name:
        logs = db.query(LogEntry).filter(
            LogEntry.user_id == user_id,
            LogEntry.service_name == incident.service_name,
            LogEntry.level.in_(["ERROR", "CRITICAL"]),
            LogEntry.timestamp.between(window_start, window_end)
        ).order_by(LogEntry.timestamp).limit(10).all()

        for log in logs:
            events.append({
                "timestamp": log.timestamp.isoformat(),
                "event_type": "error_log",
                "description": f"[{log.level}] {log.message[:100]}",
                "metadata": {"service": log.service_name, "level": log.level}
            })

    # 6. Root cause identified (if available)
    if incident.root_cause:
        events.append({
            "timestamp": (incident.resolved_at or detected).isoformat(),
            "event_type": "diagnosis",
            "description": f"Root cause identified: {incident.root_cause}",
            "metadata": {}
        })

    # 7. Resolution
    if incident.resolved_at:
        events.append({
            "timestamp": incident.resolved_at.isoformat(),
            "event_type": "resolution",
            "description": f"Incident resolved. Solution: {incident.solution or 'N/A'}",
            "metadata": {"resolution_time_seconds": incident.resolution_time_seconds}
        })

    # Sort by timestamp
    events.sort(key=lambda e: e["timestamp"])
    return events
