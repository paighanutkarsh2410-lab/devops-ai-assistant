"""
Post-Incident Review (PIR) Generator.
Uses Claude AI to auto-generate blameless post-mortem reports from incident data.
"""
import os
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from models.user import User
from utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/postmortem", tags=["postmortem"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _get_incident_context(incident_id: str, db: Session) -> dict:
    """Gather all context about an incident for the post-mortem."""
    from models.incident import Incident
    from models.action_log import ActionLog

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {}

    # Get action logs for this incident
    actions = []
    try:
        action_logs = db.query(ActionLog).filter(
            ActionLog.incident_id == incident_id
        ).order_by(ActionLog.created_at.asc()).all()
        actions = [
            {
                "action": a.action_type,
                "agent": a.agent_name,
                "status": a.status,
                "details": a.details,
                "timestamp": a.created_at.isoformat() if a.created_at else "",
            }
            for a in action_logs
        ]
    except Exception:
        pass

    return {
        "id": str(incident.id),
        "title": incident.title,
        "description": incident.description or "",
        "severity": incident.severity,
        "status": incident.status,
        "service_name": incident.service_name,
        "root_cause": incident.root_cause or "Not yet determined",
        "created_at": incident.created_at.isoformat() if incident.created_at else "",
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else "",
        "detection_method": getattr(incident, "detection_method", "automated"),
        "actions_taken": actions,
    }


def _generate_with_ai(context: dict) -> dict:
    """Generate post-mortem using Claude AI."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = f"""Generate a blameless post-incident review (post-mortem) report for this infrastructure incident.
Focus on systemic improvements, not individual blame.

Incident Details:
- Title: {context.get('title', 'Unknown')}
- Severity: {context.get('severity', 'unknown')}
- Service: {context.get('service_name', 'unknown')}
- Description: {context.get('description', 'N/A')}
- Root Cause: {context.get('root_cause', 'Not determined')}
- Detected: {context.get('created_at', 'unknown')}
- Resolved: {context.get('resolved_at', 'unknown')}
- Actions Taken: {json.dumps(context.get('actions_taken', [])[:10], indent=2)}

Generate a JSON response with this exact structure:
{{
  "summary": "2-3 sentence executive summary of what happened and impact",
  "timeline": [
    {{"time": "HH:MM", "event": "description of what happened"}},
  ],
  "root_cause_analysis": "Detailed explanation of what caused the incident",
  "contributing_factors": ["factor 1", "factor 2"],
  "impact": {{
    "duration_description": "how long the impact lasted",
    "affected_services": ["list of services affected"],
    "user_impact": "description of user-facing impact",
    "severity_justification": "why this severity level was appropriate"
  }},
  "what_went_well": ["thing 1", "thing 2"],
  "what_went_wrong": ["thing 1", "thing 2"],
  "action_items": [
    {{"action": "description", "priority": "P1/P2/P3", "owner": "team/role", "due": "timeframe"}},
  ],
  "lessons_learned": ["lesson 1", "lesson 2"],
  "prevention_measures": ["measure 1", "measure 2"]
}}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text

        # Extract JSON from response
        try:
            # Try direct parse
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"summary": text, "error": "Could not parse structured response"}

        return result

    except Exception as e:
        logger.error(f"AI post-mortem generation failed: {e}")
        return None


def _generate_fallback(context: dict) -> dict:
    """Generate a template-based post-mortem when AI is unavailable."""
    created = context.get("created_at", "")
    resolved = context.get("resolved_at", "")

    # Calculate duration
    duration = "Unknown"
    if created and resolved:
        try:
            t_start = datetime.fromisoformat(created.replace("Z", "+00:00"))
            t_end = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
            diff = t_end - t_start
            minutes = diff.total_seconds() / 60
            if minutes < 60:
                duration = f"{minutes:.0f} minutes"
            else:
                duration = f"{minutes / 60:.1f} hours"
        except (ValueError, TypeError):
            pass

    actions = context.get("actions_taken", [])
    timeline = []
    for a in actions:
        timeline.append({
            "time": a.get("timestamp", "")[:16].replace("T", " "),
            "event": f"{a.get('agent', 'System')}: {a.get('action', 'Unknown action')} — {a.get('status', 'unknown')}",
        })

    if not timeline:
        timeline = [
            {"time": created[:16].replace("T", " ") if created else "—", "event": "Incident detected"},
            {"time": resolved[:16].replace("T", " ") if resolved else "—", "event": "Incident resolved"},
        ]

    return {
        "summary": f"{context.get('severity', 'unknown').upper()} severity incident on {context.get('service_name', 'unknown service')}: {context.get('title', 'Unknown incident')}. Root cause: {context.get('root_cause', 'under investigation')}.",
        "timeline": timeline,
        "root_cause_analysis": context.get("root_cause", "Root cause analysis pending. Manual investigation recommended."),
        "contributing_factors": [
            "Details require further investigation",
            "Review monitoring gaps that delayed detection",
        ],
        "impact": {
            "duration_description": duration,
            "affected_services": [context.get("service_name", "unknown")],
            "user_impact": "Impact assessment pending",
            "severity_justification": f"Classified as {context.get('severity', 'unknown')} based on service criticality and detection signals",
        },
        "what_went_well": [
            "Automated detection triggered alert",
            f"Incident was resolved within {duration}",
        ],
        "what_went_wrong": [
            "Root cause requires deeper investigation",
            "Review if earlier warning signs were missed",
        ],
        "action_items": [
            {"action": "Complete root cause analysis", "priority": "P1", "owner": "On-call engineer", "due": "48 hours"},
            {"action": "Review monitoring coverage for this failure mode", "priority": "P2", "owner": "SRE team", "due": "1 week"},
            {"action": "Update runbooks with resolution steps", "priority": "P3", "owner": "Platform team", "due": "2 weeks"},
        ],
        "lessons_learned": [
            "Document findings after root cause analysis is complete",
        ],
        "prevention_measures": [
            "Add targeted monitoring for this failure mode",
            "Consider automated remediation for similar incidents",
        ],
        "generated_by": "template",
    }


@router.post("/generate/{incident_id}")
def generate_postmortem(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a post-incident review report for an incident."""
    context = _get_incident_context(incident_id, db)
    if not context:
        raise HTTPException(404, "Incident not found")

    # Try AI generation first, fall back to template
    report = None
    if ANTHROPIC_API_KEY:
        report = _generate_with_ai(context)

    if not report:
        report = _generate_fallback(context)

    return {
        "incident_id": incident_id,
        "incident_title": context.get("title", ""),
        "incident_severity": context.get("severity", ""),
        "service_name": context.get("service_name", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "claude_ai" if ANTHROPIC_API_KEY and "generated_by" not in report else "template",
        "report": report,
    }


@router.get("/templates")
def get_templates(user: User = Depends(get_current_user)):
    """Get available post-mortem templates."""
    return {
        "templates": [
            {
                "id": "standard",
                "name": "Standard Post-Mortem",
                "description": "Comprehensive blameless post-incident review with timeline, root cause, and action items",
                "sections": ["summary", "timeline", "root_cause_analysis", "impact", "what_went_well", "what_went_wrong", "action_items", "lessons_learned", "prevention_measures"],
            },
            {
                "id": "brief",
                "name": "Brief Summary",
                "description": "Quick summary for low-severity incidents",
                "sections": ["summary", "root_cause_analysis", "action_items"],
            },
        ]
    }
