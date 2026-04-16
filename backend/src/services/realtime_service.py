"""Real-time notification service — pushes updates through WebSocket."""
from websocket.connection_manager import (
    manager,
    MSG_NEW_INCIDENT, MSG_INCIDENT_UPDATED, MSG_INCIDENT_RESOLVED,
    MSG_REMEDIATION_STARTED, MSG_REMEDIATION_COMPLETED,
    MSG_DIAGNOSTIC_PROGRESS, MSG_PREDICTION_ALERT,
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RealtimeService:
    """Pushes real-time updates to connected WebSocket clients."""

    async def notify_incident_created(self, incident: dict):
        """Broadcast new incident to all dashboard viewers."""
        await manager.broadcast_to_all({
            "type": MSG_NEW_INCIDENT,
            "data": {
                "id": str(incident.get("id", "")),
                "title": incident.get("title", ""),
                "severity": incident.get("severity", ""),
                "status": incident.get("status", "open"),
                "service_name": incident.get("service_name", ""),
                "detected_at": incident.get("detected_at", datetime.utcnow().isoformat()),
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Also broadcast to service-specific subscribers
        service = incident.get("service_name")
        if service:
            await manager.broadcast_by_service(service, {
                "type": MSG_NEW_INCIDENT,
                "data": incident,
            })

    async def notify_incident_updated(self, incident_id: str, changes: dict):
        """Send delta update — only what changed."""
        await manager.broadcast_to_all({
            "type": MSG_INCIDENT_UPDATED,
            "data": {
                "incident_id": incident_id,
                "changes": changes,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_incident_resolved(self, incident_id: str, resolution: dict):
        """Broadcast incident resolution."""
        await manager.broadcast_to_all({
            "type": MSG_INCIDENT_RESOLVED,
            "data": {
                "incident_id": incident_id,
                "auto_resolved": resolution.get("auto_resolved", False),
                "resolution_time_seconds": resolution.get("resolution_time_seconds"),
                "solution": resolution.get("solution", ""),
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_diagnostic_progress(self, incident_id: str, step: str, progress: int = 0):
        """Send diagnostic progress steps."""
        steps = {
            "analyzing_metrics": "Analyzing metrics...",
            "querying_logs": "Querying logs...",
            "correlating": "Correlating with deployments...",
            "ai_analysis": "AI analyzing root cause...",
            "complete": "Root cause identified!",
        }
        await manager.broadcast_to_all({
            "type": MSG_DIAGNOSTIC_PROGRESS,
            "data": {
                "incident_id": incident_id,
                "step": step,
                "message": steps.get(step, step),
                "progress": progress,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_remediation_progress(self, incident_id: str, step: str, action: str = ""):
        """Send remediation progress updates."""
        steps = {
            "checkpoint": "Creating checkpoint...",
            "executing": f"Executing: {action}...",
            "monitoring": "Monitoring impact...",
            "verifying": "Verification complete!",
            "rollback": "Rolling back changes...",
        }
        await manager.broadcast_to_all({
            "type": MSG_REMEDIATION_STARTED if step in ("checkpoint", "executing") else MSG_REMEDIATION_COMPLETED,
            "data": {
                "incident_id": incident_id,
                "step": step,
                "message": steps.get(step, step),
                "action": action,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_prediction_alert(self, alert: dict):
        """Broadcast predictive alert."""
        await manager.broadcast_to_all({
            "type": MSG_PREDICTION_ALERT,
            "data": alert,
            "timestamp": datetime.utcnow().isoformat(),
        })


# Singleton
realtime = RealtimeService()
