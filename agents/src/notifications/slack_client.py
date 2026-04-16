"""
Slack integration for incident notifications and interactive actions.
Uses Slack Incoming Webhooks and Bot API for rich messages.
"""
import os
import json
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#devops-alerts")

SEVERITY_COLORS = {
    "critical": "#FF0000",
    "high": "#FF6600",
    "medium": "#FFAA00",
    "low": "#00AA00",
}

SEVERITY_EMOJI = {
    "critical": ":rotating_light:",
    "high": ":warning:",
    "medium": ":large_yellow_circle:",
    "low": ":information_source:",
}


class SlackNotifier:
    """Sends rich, interactive notifications to Slack."""

    def __init__(self, webhook_url: str = None, bot_token: str = None):
        self.webhook_url = webhook_url or SLACK_WEBHOOK_URL
        self.bot_token = bot_token or SLACK_BOT_TOKEN
        self._message_cache: Dict[str, str] = {}  # incident_id → message_ts

    @property
    def available(self) -> bool:
        return bool(self.webhook_url or self.bot_token)

    # ── Incident Notifications ─────────────────────────────────────────

    def send_incident_notification(self, incident: dict) -> Optional[dict]:
        """
        Send a rich incident notification to Slack.

        Args:
            incident: Dict with id, title, severity, service_name, detected_at, metrics.

        Returns:
            Slack API response or None if unavailable.
        """
        severity = incident.get("severity", "low")
        emoji = SEVERITY_EMOJI.get(severity, ":bell:")
        color = SEVERITY_COLORS.get(severity, "#CCCCCC")
        inc_id = incident.get("id", "unknown")
        detected = incident.get("detected_at", datetime.now(timezone.utc).isoformat())

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Incident Detected — {severity.upper()}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Title:*\n{incident.get('title', 'Unknown')}"},
                    {"type": "mrkdwn", "text": f"*Service:*\n{incident.get('service_name', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Detected:*\n{detected[:19]}"},
                ],
            },
        ]

        # Add description if available
        desc = incident.get("description", "")
        if desc:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Description:*\n{desc[:500]}"},
            })

        # Add metrics if available
        metrics = incident.get("metrics", {})
        if metrics:
            metric_text = " | ".join(f"`{k}`: {v}" for k, v in metrics.items())
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Metrics:* {metric_text}"},
            })

        # Action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Details"},
                    "url": f"http://localhost:3000/dashboard?incident={inc_id}",
                    "style": "primary",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Acknowledge"},
                    "action_id": f"ack_incident_{inc_id}",
                    "value": inc_id,
                },
            ],
        })

        payload = {
            "channel": SLACK_CHANNEL,
            "text": f"{emoji} [{severity.upper()}] {incident.get('title', 'Incident')}",
            "blocks": blocks,
            "attachments": [{"color": color, "blocks": []}],
        }

        result = self._send(payload)
        if result and result.get("ts"):
            self._message_cache[inc_id] = result["ts"]
        return result

    # ── Remediation Updates ────────────────────────────────────────────

    def send_remediation_update(
        self, incident_id: str, status: str, details: dict = None
    ) -> Optional[dict]:
        """
        Send remediation status as a thread reply to the original incident.

        Args:
            incident_id: ID of the incident.
            status: started, in_progress, completed, failed.
            details: Action taken, before/after metrics, duration, etc.
        """
        details = details or {}
        status_emoji = {
            "started": ":wrench:",
            "in_progress": ":hourglass_flowing_sand:",
            "completed": ":white_check_mark:",
            "failed": ":x:",
        }

        emoji = status_emoji.get(status, ":gear:")
        action = details.get("action_name", "Unknown action")
        duration = details.get("duration_seconds", 0)

        text = f"{emoji} *Remediation {status.upper()}*\n"
        text += f"• Action: `{action}`\n"

        if status == "completed":
            text += f"• Duration: {duration:.1f}s\n"
            if details.get("before_metrics") and details.get("after_metrics"):
                text += "\n*Before → After:*\n"
                before = details["before_metrics"]
                after = details["after_metrics"]
                for key in before:
                    if key in after:
                        text += f"  `{key}`: {before[key]} → {after[key]}\n"
        elif status == "failed":
            text += f"• Error: {details.get('error', 'Unknown')}\n"
            text += f"• Rollback: {'Yes' if details.get('rollback') else 'No'}\n"

        payload = {
            "channel": SLACK_CHANNEL,
            "text": text,
        }

        # Thread reply if we have the original message
        thread_ts = self._message_cache.get(incident_id)
        if thread_ts:
            payload["thread_ts"] = thread_ts

        return self._send(payload)

    # ── Approval Requests ──────────────────────────────────────────────

    def send_approval_request(self, approval: dict) -> Optional[dict]:
        """
        Send an interactive approval request with Approve/Reject buttons.

        Args:
            approval: Dict with id, incident_id, action_name, risk_level, etc.
        """
        risk = approval.get("risk_level", "MEDIUM")
        risk_emoji = {"LOW": ":large_green_circle:", "MEDIUM": ":large_yellow_circle:", "HIGH": ":red_circle:"}

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":lock: Approval Required"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Action:*\n`{approval.get('action_name', 'Unknown')}`"},
                    {"type": "mrkdwn", "text": f"*Risk Level:*\n{risk_emoji.get(risk, ':question:')} {risk}"},
                    {"type": "mrkdwn", "text": f"*Incident:*\n{approval.get('incident_id', 'N/A')[:8]}..."},
                    {"type": "mrkdwn", "text": f"*Expires:*\n{approval.get('expiry_minutes', 30)} minutes"},
                ],
            },
        ]

        desc = approval.get("action_description", "")
        if desc:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Details:*\n{desc}"},
            })

        approval_id = approval.get("id", "unknown")
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "action_id": f"approve_{approval_id}",
                    "value": approval_id,
                    "style": "primary",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "action_id": f"reject_{approval_id}",
                    "value": approval_id,
                    "style": "danger",
                },
            ],
        })

        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f":clock3: Auto-expires in {approval.get('expiry_minutes', 30)} minutes"},
            ],
        })

        payload = {
            "channel": SLACK_CHANNEL,
            "text": f":lock: Approval needed: {approval.get('action_name', 'action')} ({risk} risk)",
            "blocks": blocks,
        }

        return self._send(payload)

    # ── Daily Summary ──────────────────────────────────────────────────

    def send_daily_summary(self, summary: dict) -> Optional[dict]:
        """
        Send a daily operations summary.

        Args:
            summary: Dict with incidents_count, auto_resolved, top_issues,
                     health_score, mttr_avg, predictions_count, etc.
        """
        health = summary.get("health_score", 0)
        health_emoji = ":green_heart:" if health >= 90 else ":yellow_heart:" if health >= 70 else ":heart:"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":newspaper: Daily Operations Summary"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incidents Yesterday:*\n{summary.get('incidents_count', 0)}"},
                    {"type": "mrkdwn", "text": f"*Auto-Resolved:*\n{summary.get('auto_resolved', 0)}"},
                    {"type": "mrkdwn", "text": f"*System Health:*\n{health_emoji} {health}%"},
                    {"type": "mrkdwn", "text": f"*Avg Resolution:*\n{summary.get('mttr_avg', 0):.0f}s"},
                ],
            },
        ]

        # Top issues
        top_issues = summary.get("top_issues", [])
        if top_issues:
            issues_text = "\n".join(f"  • {issue}" for issue in top_issues[:5])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Top Issues:*\n{issues_text}"},
            })

        # Predictions
        predictions = summary.get("predictions_count", 0)
        if predictions > 0:
            prevented = summary.get("prevented_count", 0)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Predictions:* {predictions} alerts, {prevented} prevented",
                },
            })

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
            ],
        })

        payload = {
            "channel": SLACK_CHANNEL,
            "text": f":newspaper: Daily Summary — {summary.get('incidents_count', 0)} incidents, health {health}%",
            "blocks": blocks,
        }

        return self._send(payload)

    # ── Predictive Alerts ──────────────────────────────────────────────

    def send_predictive_alert(self, prediction: dict) -> Optional[dict]:
        """
        Send a predictive alert (different formatting from reactive alerts).

        Args:
            prediction: Dict with title, prediction_type, service_name,
                        hours_until_issue, confidence, preventive_actions, etc.
        """
        hours = prediction.get("hours_until_issue") or prediction.get("hours_until_breach", 0)
        confidence = prediction.get("confidence", 0)
        pred_type = prediction.get("prediction_type", "unknown")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":crystal_ball: Predictive Alert"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Prediction:*\n{prediction.get('title', 'Unknown')}"},
                    {"type": "mrkdwn", "text": f"*Type:*\n{pred_type.replace('_', ' ').title()}"},
                    {"type": "mrkdwn", "text": f"*Time Until Issue:*\n{hours:.0f} hours"},
                    {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence}%"},
                ],
            },
        ]

        # Service
        service = prediction.get("service_name")
        if service:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Service:* `{service}`"},
            })

        # Preventive actions
        actions = prediction.get("preventive_actions", [])
        if actions:
            actions_text = "\n".join(
                f"  • {a.get('description', a.get('action', 'Unknown'))}"
                for a in actions[:3]
            )
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Recommended Actions:*\n{actions_text}"},
            })

        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": ":crystal_ball: This is a *prediction*, not a current issue. Take preventive action now."},
            ],
        })

        payload = {
            "channel": SLACK_CHANNEL,
            "text": f":crystal_ball: Prediction: {prediction.get('title', '')} ({hours:.0f}h)",
            "blocks": blocks,
        }

        return self._send(payload)

    # ── Interactive Button Handling ─────────────────────────────────────

    def handle_interaction(self, payload: dict) -> dict:
        """
        Handle Slack interactive button clicks.

        Args:
            payload: Slack interaction payload with action_id, value, user, etc.

        Returns:
            Response dict with action taken.
        """
        actions = payload.get("actions", [])
        user = payload.get("user", {}).get("name", "unknown")

        for action in actions:
            action_id = action.get("action_id", "")
            value = action.get("value", "")

            if action_id.startswith("ack_incident_"):
                return {
                    "action": "acknowledge",
                    "incident_id": value,
                    "user": user,
                    "message": f"Incident acknowledged by {user}",
                }

            elif action_id.startswith("approve_"):
                return {
                    "action": "approve",
                    "approval_id": value,
                    "user": user,
                    "message": f"Action approved by {user}",
                }

            elif action_id.startswith("reject_"):
                return {
                    "action": "reject",
                    "approval_id": value,
                    "user": user,
                    "message": f"Action rejected by {user}",
                }

        return {"action": "unknown", "message": "Unrecognized interaction"}

    # ── Internal ───────────────────────────────────────────────────────

    def _send(self, payload: dict) -> Optional[dict]:
        """Send a message to Slack via webhook or Bot API."""
        if not self.available:
            logger.debug(f"Slack not configured — message suppressed: {payload.get('text', '')[:80]}")
            return None

        try:
            if self.bot_token:
                resp = requests.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10,
                )
                data = resp.json()
                if not data.get("ok"):
                    logger.warning(f"Slack API error: {data.get('error')}")
                return data
            else:
                resp = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10,
                )
                return {"ok": resp.status_code == 200, "status": resp.status_code}

        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return None
