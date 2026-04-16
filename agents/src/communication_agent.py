"""
Communication Agent: Manages all notifications across channels.
Routes events to Slack, email, and other channels based on severity,
user preferences, and smart anti-spam rules.
"""
import sys
import os
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from base_agent import BaseAgent
from notifications.slack_client import SlackNotifier
from notifications.email_client import EmailNotifier

logger = logging.getLogger(__name__)

# Channel routing by severity
DEFAULT_ROUTING = {
    "critical": ["slack", "email"],
    "high": ["slack", "email"],
    "medium": ["slack"],
    "low": ["digest"],
}

# Quiet hours: suppress non-critical notifications
QUIET_START = 23  # 11 PM
QUIET_END = 7     # 7 AM


class CommunicationAgent(BaseAgent):
    """Agent that manages all notification delivery across channels."""

    def __init__(self):
        super().__init__("CommunicationAgent")
        self.slack = SlackNotifier()
        self.email = EmailNotifier()

        # Anti-spam tracking
        self._recent_notifications: List[dict] = []
        self._rate_limits: Dict[str, datetime] = {}  # channel → last_sent
        self._digest_buffer: List[dict] = []  # Low severity, sent in daily digest
        self._notification_log: List[dict] = []

        # Rate limits per channel (seconds between messages)
        self._rate_limit_seconds = {
            "slack": 5,
            "email": 60,
        }

    def tick(self):
        """
        Periodic check — sends daily summary at 9 AM UTC.
        Called by orchestrator every 300s (5 min).
        """
        now = datetime.now(timezone.utc)

        # Daily summary at 9:00 AM
        if now.hour == 9 and now.minute < 5:
            self._send_daily_summary()

    # ── Main Notification Entry Point ──────────────────────────────────

    def notify(self, event: dict, channels: List[str] = None) -> Dict[str, Any]:
        """
        Route an event to appropriate notification channels.

        Args:
            event: Dict with type, severity, data, etc.
            channels: Override channels. If None, uses smart routing.

        Returns:
            Dict with delivery results per channel.
        """
        event_type = event.get("type", "unknown")
        severity = event.get("severity", "low")
        data = event.get("data", {})

        # Determine channels
        if channels is None:
            channels = self._determine_channels(event)

        # Anti-spam check
        if self._is_duplicate(event):
            logger.debug(f"Duplicate notification suppressed: {event_type}")
            return {"suppressed": True, "reason": "duplicate"}

        # Quiet hours check (allow critical through)
        if self._is_quiet_hours() and severity not in ("critical", "high"):
            self._digest_buffer.append(event)
            return {"buffered": True, "reason": "quiet_hours"}

        results = {}
        for channel in channels:
            if channel == "digest":
                self._digest_buffer.append(event)
                results["digest"] = {"status": "buffered"}
                continue

            # Rate limit check
            if self._is_rate_limited(channel):
                results[channel] = {"status": "rate_limited"}
                continue

            result = self._send_to_channel(channel, event_type, data, severity)
            results[channel] = result
            self._record_notification(event, channel, result)

        return results

    # ── Event Handlers ─────────────────────────────────────────────────

    def handle_incident_detected(self, incident: dict):
        """Handle a new incident detection."""
        return self.notify({
            "type": "incident_detected",
            "severity": incident.get("severity", "medium"),
            "data": incident,
        })

    def handle_incident_diagnosed(self, incident: dict, diagnosis: dict):
        """Handle diagnosis completion."""
        return self.notify({
            "type": "incident_diagnosed",
            "severity": incident.get("severity", "medium"),
            "data": {**incident, "diagnosis": diagnosis},
        })

    def handle_remediation_started(self, incident_id: str, action: str):
        """Handle remediation start."""
        self.slack.send_remediation_update(incident_id, "started", {
            "action_name": action,
        })

    def handle_remediation_completed(
        self, incident_id: str, action: str, success: bool, details: dict = None
    ):
        """Handle remediation completion."""
        status = "completed" if success else "failed"
        self.slack.send_remediation_update(incident_id, status, {
            "action_name": action,
            **(details or {}),
        })

    def handle_approval_required(self, approval: dict):
        """Handle approval request."""
        return self.notify({
            "type": "approval_required",
            "severity": "high",
            "data": approval,
        })

    def handle_predictive_alert(self, prediction: dict):
        """Handle a predictive alert."""
        return self.notify({
            "type": "predictive_alert",
            "severity": prediction.get("severity", "medium"),
            "data": prediction,
        })

    # ── Channel Routing ────────────────────────────────────────────────

    def _determine_channels(self, event: dict) -> List[str]:
        """
        Determine which channels to send to based on severity and event type.
        """
        severity = event.get("severity", "low")
        event_type = event.get("type", "")

        # Predictive alerts go to digest unless critical
        if event_type == "predictive_alert" and severity not in ("critical", "high"):
            return ["digest"]

        # Approval requests always go to Slack (interactive buttons)
        if event_type == "approval_required":
            return ["slack"]

        # Daily/weekly reports only email
        if event_type in ("daily_summary", "weekly_report"):
            return ["email"]

        return DEFAULT_ROUTING.get(severity, ["slack"])

    def determine_recipients(self, event: dict) -> List[str]:
        """
        Determine email recipients based on event properties.

        Args:
            event: Event dict with severity, service, etc.

        Returns:
            List of email addresses.
        """
        # Try to fetch preferences from backend
        recipients = []
        try:
            prefs = self.api_get("/preferences/notifications")
            if isinstance(prefs, list):
                severity = event.get("severity", "low")
                service = event.get("data", {}).get("service_name", "")
                severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                event_level = severity_order.get(severity, 3)

                for pref in prefs:
                    if not pref.get("enabled"):
                        continue
                    threshold = severity_order.get(pref.get("severity_threshold", "low"), 3)
                    if event_level <= threshold:
                        services = pref.get("services", [])
                        if not services or service in services:
                            recipients.append(pref.get("email", ""))
        except Exception:
            pass

        return [r for r in recipients if r]

    # ── Message Formatting ─────────────────────────────────────────────

    def _send_to_channel(
        self, channel: str, event_type: str, data: dict, severity: str
    ) -> dict:
        """Send a formatted message to a specific channel."""
        try:
            if channel == "slack":
                return self._send_slack(event_type, data, severity)
            elif channel == "email":
                return self._send_email(event_type, data, severity)
            else:
                return {"status": "unknown_channel", "channel": channel}
        except Exception as e:
            logger.error(f"Failed to send to {channel}: {e}")
            return {"status": "error", "error": str(e)}

    def _send_slack(self, event_type: str, data: dict, severity: str) -> dict:
        """Route to the appropriate Slack notification method."""
        result = None

        if event_type == "incident_detected":
            result = self.slack.send_incident_notification(data)
        elif event_type == "approval_required":
            result = self.slack.send_approval_request(data)
        elif event_type == "predictive_alert":
            result = self.slack.send_predictive_alert(data)
        elif event_type == "daily_summary":
            result = self.slack.send_daily_summary(data)
        else:
            # Generic Slack message for other event types
            result = self.slack._send({
                "text": f"[{severity.upper()}] {event_type}: {data.get('title', data.get('message', 'Event'))}",
            })

        self._rate_limits["slack"] = datetime.now(timezone.utc)
        return {"status": "sent" if result else "no_config", "result": result}

    def _send_email(self, event_type: str, data: dict, severity: str) -> dict:
        """Route to the appropriate email notification method."""
        recipients = self.determine_recipients({"severity": severity, "data": data})

        # Fallback: if no recipients configured, skip
        if not recipients:
            return {"status": "no_recipients"}

        result = None

        if event_type == "incident_detected":
            if severity in ("critical", "high"):
                result = self.email.send_critical_alert(data, recipients)
            else:
                result = self.email.send_incident_email(data, recipients)
        elif event_type == "weekly_report":
            for r in recipients:
                result = self.email.send_weekly_digest(r, data)
        else:
            result = self.email.send_incident_email(
                {**data, "title": f"{event_type}: {data.get('title', 'Event')}"},
                recipients,
            )

        self._rate_limits["email"] = datetime.now(timezone.utc)
        return {"status": "sent" if result else "no_config", "result": result}

    # ── Daily Summary ──────────────────────────────────────────────────

    def _send_daily_summary(self):
        """Generate and send daily summary from backend data."""
        try:
            # Fetch yesterday's stats
            incidents = self.api_get("/incidents/?limit=100") or []
            alerts = self.api_get("/alerts/") or []

            now = datetime.now(timezone.utc)
            yesterday = now - timedelta(days=1)

            recent_incidents = [
                i for i in incidents
                if i.get("detected_at", "")[:10] == yesterday.strftime("%Y-%m-%d")
            ]

            auto_resolved = sum(
                1 for i in recent_incidents
                if i.get("status") == "resolved"
            )

            # Build summary
            summary = {
                "incidents_count": len(recent_incidents),
                "auto_resolved": auto_resolved,
                "health_score": max(0, 100 - len(recent_incidents) * 5),
                "mttr_avg": 0,
                "top_issues": [i.get("title", "") for i in recent_incidents[:5]],
                "predictions_count": len([a for a in alerts if a.get("prediction_type")]),
                "prevented_count": 0,
            }

            # Include buffered digest items
            if self._digest_buffer:
                summary["digest_items"] = len(self._digest_buffer)
                self._digest_buffer.clear()

            self.slack.send_daily_summary(summary)

        except Exception as e:
            logger.error(f"Daily summary failed: {e}")

    # ── Anti-Spam ──────────────────────────────────────────────────────

    def _is_duplicate(self, event: dict) -> bool:
        """Check if this notification was recently sent (within 5 min)."""
        key = f"{event.get('type')}:{event.get('data', {}).get('id', '')}"
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Clean old entries
        self._recent_notifications = [
            n for n in self._recent_notifications
            if n.get("time", datetime.min) > cutoff
        ]

        # Check for duplicate
        for n in self._recent_notifications:
            if n.get("key") == key:
                return True

        self._recent_notifications.append({"key": key, "time": datetime.now(timezone.utc)})
        return False

    def _is_rate_limited(self, channel: str) -> bool:
        """Check if channel is rate-limited."""
        last_sent = self._rate_limits.get(channel)
        if not last_sent:
            return False

        limit_seconds = self._rate_limit_seconds.get(channel, 10)
        return (datetime.now(timezone.utc) - last_sent).total_seconds() < limit_seconds

    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        hour = datetime.now(timezone.utc).hour
        if QUIET_START > QUIET_END:
            return hour >= QUIET_START or hour < QUIET_END
        return QUIET_START <= hour < QUIET_END

    # ── Logging ────────────────────────────────────────────────────────

    def _record_notification(self, event: dict, channel: str, result: dict):
        """Log notification delivery for tracking."""
        self._notification_log.append({
            "event_type": event.get("type"),
            "severity": event.get("severity"),
            "channel": channel,
            "status": result.get("status"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Keep last 1000 entries
        if len(self._notification_log) > 1000:
            self._notification_log = self._notification_log[-500:]

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification delivery statistics."""
        total = len(self._notification_log)
        sent = sum(1 for n in self._notification_log if n["status"] == "sent")
        by_channel = defaultdict(int)
        by_type = defaultdict(int)

        for n in self._notification_log:
            by_channel[n["channel"]] += 1
            by_type[n["event_type"]] += 1

        return {
            "total_notifications": total,
            "sent": sent,
            "suppressed": total - sent,
            "by_channel": dict(by_channel),
            "by_type": dict(by_type),
            "digest_buffered": len(self._digest_buffer),
        }
