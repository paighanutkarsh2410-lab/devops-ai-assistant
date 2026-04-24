"""
Email notification system using Resend API.
Sends incident alerts, weekly digests, and critical notifications.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "SentryAI <alerts@sentryai.system>")

try:
    import resend
    resend.api_key = RESEND_API_KEY
    RESEND_AVAILABLE = bool(RESEND_API_KEY)
except ImportError:
    RESEND_AVAILABLE = False
    logger.info("Resend not installed — email notifications disabled")


class EmailNotifier:
    """Sends HTML email notifications via Resend API."""

    def __init__(self, api_key: str = None):
        if api_key:
            self._api_key = api_key
            if RESEND_AVAILABLE:
                resend.api_key = api_key
        else:
            self._api_key = RESEND_API_KEY
        self._from_email = FROM_EMAIL

    @property
    def available(self) -> bool:
        return RESEND_AVAILABLE and bool(self._api_key)

    # ── Incident Email ─────────────────────────────────────────────────

    def send_incident_email(
        self, incident: dict, recipients: List[str]
    ) -> Optional[dict]:
        """
        Send a detailed incident notification email.

        Args:
            incident: Incident data dict.
            recipients: List of email addresses.
        """
        severity = incident.get("severity", "low")
        title = incident.get("title", "Incident Detected")
        service = incident.get("service_name", "Unknown")
        detected = incident.get("detected_at", datetime.now(timezone.utc).isoformat())
        description = incident.get("description", "No description provided.")
        inc_id = incident.get("id", "unknown")

        html = self._render_template("incident", {
            "title": title,
            "severity": severity,
            "service": service,
            "detected": detected[:19].replace("T", " "),
            "description": description,
            "incident_id": inc_id,
            "dashboard_url": f"http://localhost:3000/dashboard?incident={inc_id}",
            "metrics": incident.get("metrics", {}),
        })

        subject = f"[{severity.upper()}] {title}"
        return self._send_email(recipients, subject, html)

    # ── Weekly Digest ──────────────────────────────────────────────────

    def send_weekly_digest(
        self, user_email: str, digest: dict
    ) -> Optional[dict]:
        """
        Send a weekly operations digest.

        Args:
            user_email: Recipient email.
            digest: Dict with stats, trends, top_incidents, insights.
        """
        html = self._render_template("weekly_digest", {
            "period": digest.get("period", "This Week"),
            "incidents_count": digest.get("incidents_count", 0),
            "auto_resolved": digest.get("auto_resolved", 0),
            "mttr_avg": digest.get("mttr_avg", 0),
            "health_score": digest.get("health_score", 0),
            "top_incidents": digest.get("top_incidents", []),
            "trends": digest.get("trends", []),
            "insights": digest.get("insights", []),
            "predictions": digest.get("predictions_count", 0),
            "prevented": digest.get("prevented_count", 0),
        })

        return self._send_email(
            [user_email],
            f"Weekly DevOps Report — {digest.get('period', 'This Week')}",
            html,
        )

    # ── Critical Alert ─────────────────────────────────────────────────

    def send_critical_alert(
        self, incident: dict, recipients: List[str]
    ) -> Optional[dict]:
        """
        Send a brief, urgent critical alert email.
        Only for critical/high severity — SMS-like brevity.
        """
        severity = incident.get("severity", "critical")
        if severity not in ("critical", "high"):
            return None

        html = self._render_template("critical_alert", {
            "title": incident.get("title", "Critical Incident"),
            "service": incident.get("service_name", "Unknown"),
            "severity": severity,
            "detected": incident.get("detected_at", "")[:19].replace("T", " "),
            "description": incident.get("description", "")[:200],
            "dashboard_url": f"http://localhost:3000/dashboard?incident={incident.get('id', '')}",
        })

        subject = f"URGENT [{severity.upper()}] {incident.get('title', 'Critical Incident')}"
        return self._send_email(recipients, subject, html, priority="high")

    # ── Template Rendering ─────────────────────────────────────────────

    def _render_template(self, template_name: str, data: dict) -> str:
        """Render an HTML email template with data."""
        templates = {
            "incident": self._incident_template,
            "weekly_digest": self._weekly_digest_template,
            "critical_alert": self._critical_alert_template,
        }

        renderer = templates.get(template_name)
        if renderer:
            return renderer(data)
        return f"<p>Template '{template_name}' not found</p>"

    def _incident_template(self, d: dict) -> str:
        severity_colors = {"critical": "#dc2626", "high": "#ea580c", "medium": "#d97706", "low": "#16a34a"}
        color = severity_colors.get(d["severity"], "#6b7280")

        metrics_html = ""
        if d.get("metrics"):
            rows = "".join(
                f"<tr><td style='padding:4px 12px;border:1px solid #e5e7eb'>{k}</td>"
                f"<td style='padding:4px 12px;border:1px solid #e5e7eb'>{v}</td></tr>"
                for k, v in d["metrics"].items()
            )
            metrics_html = f"""
            <h3 style="margin-top:20px">Metrics</h3>
            <table style="border-collapse:collapse">{rows}</table>
            """

        return f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
            <div style="background:{color};color:white;padding:16px 24px;border-radius:8px 8px 0 0">
                <h2 style="margin:0">[{d['severity'].upper()}] Incident Detected</h2>
            </div>
            <div style="border:1px solid #e5e7eb;border-top:none;padding:24px;border-radius:0 0 8px 8px">
                <h3 style="margin-top:0">{d['title']}</h3>
                <table style="width:100%">
                    <tr><td style="color:#6b7280">Service:</td><td><strong>{d['service']}</strong></td></tr>
                    <tr><td style="color:#6b7280">Detected:</td><td>{d['detected']}</td></tr>
                    <tr><td style="color:#6b7280">Severity:</td><td style="color:{color}"><strong>{d['severity'].upper()}</strong></td></tr>
                </table>
                <p style="margin-top:16px">{d['description']}</p>
                {metrics_html}
                <div style="margin-top:24px">
                    <a href="{d['dashboard_url']}" style="background:{color};color:white;padding:10px 20px;
                       text-decoration:none;border-radius:6px;display:inline-block">View in Dashboard</a>
                </div>
            </div>
            <p style="color:#9ca3af;font-size:12px;text-align:center;margin-top:16px">
                SentryAI — Automated Incident Notification
            </p>
        </div>
        """

    def _weekly_digest_template(self, d: dict) -> str:
        health = d.get("health_score", 0)
        health_color = "#16a34a" if health >= 90 else "#d97706" if health >= 70 else "#dc2626"

        incidents_html = ""
        for inc in d.get("top_incidents", [])[:5]:
            incidents_html += f"<li>{inc}</li>"

        insights_html = ""
        for insight in d.get("insights", [])[:3]:
            insights_html += f"<li>{insight}</li>"

        return f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
            <div style="background:#1e40af;color:white;padding:16px 24px;border-radius:8px 8px 0 0">
                <h2 style="margin:0">Weekly Operations Report</h2>
                <p style="margin:4px 0 0;opacity:0.8">{d['period']}</p>
            </div>
            <div style="border:1px solid #e5e7eb;border-top:none;padding:24px;border-radius:0 0 8px 8px">
                <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px">
                    <div style="flex:1;min-width:120px;background:#f3f4f6;padding:12px;border-radius:8px;text-align:center">
                        <div style="font-size:24px;font-weight:bold">{d['incidents_count']}</div>
                        <div style="color:#6b7280;font-size:12px">Incidents</div>
                    </div>
                    <div style="flex:1;min-width:120px;background:#f3f4f6;padding:12px;border-radius:8px;text-align:center">
                        <div style="font-size:24px;font-weight:bold">{d['auto_resolved']}</div>
                        <div style="color:#6b7280;font-size:12px">Auto-Resolved</div>
                    </div>
                    <div style="flex:1;min-width:120px;background:#f3f4f6;padding:12px;border-radius:8px;text-align:center">
                        <div style="font-size:24px;font-weight:bold;color:{health_color}">{health}%</div>
                        <div style="color:#6b7280;font-size:12px">Health Score</div>
                    </div>
                    <div style="flex:1;min-width:120px;background:#f3f4f6;padding:12px;border-radius:8px;text-align:center">
                        <div style="font-size:24px;font-weight:bold">{d['mttr_avg']:.0f}s</div>
                        <div style="color:#6b7280;font-size:12px">Avg Resolution</div>
                    </div>
                </div>
                {"<h3>Top Incidents</h3><ul>" + incidents_html + "</ul>" if incidents_html else ""}
                {"<h3>Insights</h3><ul>" + insights_html + "</ul>" if insights_html else ""}
                <p style="color:#6b7280;margin-top:16px">Predictions: {d['predictions']} alerts, {d['prevented']} prevented</p>
            </div>
            <p style="color:#9ca3af;font-size:12px;text-align:center;margin-top:16px">
                SentryAI — Weekly Digest
            </p>
        </div>
        """

    def _critical_alert_template(self, d: dict) -> str:
        return f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
            <div style="background:#dc2626;color:white;padding:20px 24px;border-radius:8px">
                <h2 style="margin:0">URGENT: {d['title']}</h2>
                <p style="margin:8px 0 0;font-size:16px">
                    Service <strong>{d['service']}</strong> — {d['severity'].upper()}
                </p>
                <p style="margin:8px 0 0;opacity:0.9">{d['description']}</p>
                <p style="margin:12px 0 0;font-size:13px;opacity:0.8">Detected: {d['detected']}</p>
                <div style="margin-top:16px">
                    <a href="{d['dashboard_url']}" style="background:white;color:#dc2626;padding:10px 20px;
                       text-decoration:none;border-radius:6px;display:inline-block;font-weight:bold">
                       View Incident →</a>
                </div>
            </div>
        </div>
        """

    # ── Send ───────────────────────────────────────────────────────────

    def _send_email(
        self, to: List[str], subject: str, html: str, priority: str = "normal"
    ) -> Optional[dict]:
        """Send an email via Resend API."""
        if not self.available:
            logger.debug(f"Email not configured — suppressed: {subject}")
            return None

        try:
            params = {
                "from": self._from_email,
                "to": to,
                "subject": subject,
                "html": html,
            }
            if priority == "high":
                params["headers"] = {"X-Priority": "1", "Importance": "high"}

            result = resend.Emails.send(params)
            logger.info(f"Email sent: {subject} → {to}")
            return result

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return None
