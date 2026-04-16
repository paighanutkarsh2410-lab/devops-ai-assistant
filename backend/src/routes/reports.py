"""API routes for learning reports, insights, and automated reporting."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from models import get_db, LearningData, ActionOutcome, Pattern
from models.incident import Incident

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/learning/weekly")
def weekly_report(db: Session = Depends(get_db)):
    """Generate a weekly learning report."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    # This week's outcomes
    weekly_outcomes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.timestamp >= week_ago
    ).scalar() or 0

    weekly_successes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.timestamp >= week_ago,
        ActionOutcome.success == True,
    ).scalar() or 0

    # Patterns discovered
    new_patterns = db.query(func.count(Pattern.id)).filter(
        Pattern.created_at >= week_ago
    ).scalar() or 0

    # Action stats for the week
    action_stats = db.query(
        ActionOutcome.action_name,
        func.count().label("total"),
        func.count().filter(ActionOutcome.success == True).label("successes"),
        func.avg(ActionOutcome.duration_seconds).label("avg_duration"),
    ).filter(
        ActionOutcome.timestamp >= week_ago
    ).group_by(ActionOutcome.action_name).all()

    actions = []
    for row in action_stats:
        total = row.total or 0
        successes = int(row.successes or 0)
        actions.append({
            "action_name": row.action_name,
            "total": total,
            "successes": successes,
            "success_rate": round(successes / total * 100, 1) if total > 0 else 0,
            "avg_duration": round(float(row.avg_duration or 0), 2),
        })

    # Top performing action
    best_action = max(actions, key=lambda x: x["success_rate"]) if actions else None

    return {
        "report_type": "weekly",
        "period_start": week_ago.isoformat(),
        "period_end": datetime.utcnow().isoformat(),
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "incidents_handled": weekly_outcomes,
            "successful_remediations": weekly_successes,
            "success_rate": round(
                weekly_successes / weekly_outcomes * 100, 1
            ) if weekly_outcomes > 0 else 0,
            "new_patterns_discovered": new_patterns,
            "top_performing_action": best_action["action_name"] if best_action else None,
        },
        "action_breakdown": sorted(actions, key=lambda x: x["total"], reverse=True),
    }


@router.get("/learning/monthly")
def monthly_report(db: Session = Depends(get_db)):
    """Generate a monthly learning report."""
    month_ago = datetime.utcnow() - timedelta(days=30)

    monthly_outcomes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.timestamp >= month_ago
    ).scalar() or 0

    monthly_successes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.timestamp >= month_ago,
        ActionOutcome.success == True,
    ).scalar() or 0

    new_patterns = db.query(func.count(Pattern.id)).filter(
        Pattern.created_at >= month_ago
    ).scalar() or 0

    # Trending patterns
    trending = db.query(Pattern).filter(
        Pattern.trending == "increasing"
    ).order_by(desc(Pattern.frequency)).limit(5).all()

    # Learning data growth
    total_learning = db.query(func.count(LearningData.id)).scalar() or 0

    avg_resolution = db.query(func.avg(ActionOutcome.duration_seconds)).filter(
        ActionOutcome.timestamp >= month_ago,
        ActionOutcome.success == True,
    ).scalar() or 0

    return {
        "report_type": "monthly",
        "period_start": month_ago.isoformat(),
        "period_end": datetime.utcnow().isoformat(),
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "incidents_handled": monthly_outcomes,
            "successful_remediations": monthly_successes,
            "success_rate": round(
                monthly_successes / monthly_outcomes * 100, 1
            ) if monthly_outcomes > 0 else 0,
            "new_patterns_discovered": new_patterns,
            "total_knowledge_entries": total_learning,
            "avg_resolution_time_seconds": round(float(avg_resolution), 2),
        },
        "trending_patterns": [
            {
                "name": p.name,
                "pattern_type": p.pattern_type,
                "frequency": p.frequency,
            }
            for p in trending
        ],
    }


@router.get("/learning/insights")
def learning_insights(db: Session = Depends(get_db)):
    """Generate human-readable learning insights."""
    insights = []

    # Overall stats
    total_outcomes = db.query(func.count(ActionOutcome.id)).scalar() or 0
    total_successes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.success == True
    ).scalar() or 0
    total_patterns = db.query(func.count(Pattern.id)).scalar() or 0

    if total_patterns > 0:
        insights.append(f"System has discovered {total_patterns} distinct incident patterns.")

    if total_outcomes > 0:
        rate = round(total_successes / total_outcomes * 100, 1)
        insights.append(f"Overall remediation success rate: {rate}%.")

    # Best action
    best = db.query(
        LearningData.action_name, LearningData.success_rate
    ).filter(
        LearningData.total_attempts >= 3
    ).order_by(desc(LearningData.success_rate)).first()

    if best:
        insights.append(f"Most effective action: {best.action_name} ({best.success_rate:.0f}% success).")

    # Average resolution
    avg_time = db.query(func.avg(ActionOutcome.duration_seconds)).filter(
        ActionOutcome.success == True
    ).scalar()
    if avg_time and avg_time > 0:
        if avg_time < 60:
            insights.append(f"Average resolution time: {avg_time:.0f} seconds.")
        else:
            insights.append(f"Average resolution time: {avg_time / 60:.1f} minutes.")

    # Low performers
    low_performers = db.query(LearningData).filter(
        LearningData.total_attempts >= 3,
        LearningData.success_rate < 40,
    ).all()
    for lp in low_performers:
        insights.append(
            f"Action '{lp.action_name}' for '{lp.pattern_type}' has low success "
            f"({lp.success_rate:.0f}%) — needs review."
        )

    if not insights:
        insights.append("Learning system is initializing. Resolve more incidents to generate insights.")

    return {"insights": insights, "generated_at": datetime.utcnow().isoformat()}


# ── Automated Reports ──────────────────────────────────────────────────

@router.get("/incident/{incident_id}/postmortem")
def incident_postmortem(incident_id: str, db: Session = Depends(get_db)):
    """Generate a post-mortem report for an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")

    inc_data = {
        "id": str(incident.id),
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity,
        "service_name": incident.service_name,
        "status": incident.status,
        "root_cause": incident.root_cause,
        "solution": incident.solution,
        "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
    }

    return {
        "type": "postmortem",
        "incident": inc_data,
        "report": _generate_postmortem_md(inc_data),
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/weekly")
def weekly_health_report(db: Session = Depends(get_db)):
    """Generate a weekly system health report."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    weekly = db.query(Incident).filter(
        Incident.detected_at >= week_ago
    ).all()

    resolved = [i for i in weekly if i.status == "resolved"]
    critical = [i for i in weekly if i.severity == "critical"]
    services = set(i.service_name for i in weekly if i.service_name)

    return {
        "type": "weekly_health",
        "period_start": week_ago.isoformat(),
        "period_end": datetime.utcnow().isoformat(),
        "stats": {
            "total_incidents": len(weekly),
            "resolved": len(resolved),
            "critical": len(critical),
            "services_affected": len(services),
            "resolution_rate": round(len(resolved) / max(len(weekly), 1) * 100, 1),
        },
        "top_incidents": [
            {"title": i.title, "severity": i.severity, "service": i.service_name, "status": i.status}
            for i in weekly[:10]
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/monthly")
def monthly_trends_report(db: Session = Depends(get_db)):
    """Generate month-over-month trends."""
    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    current = db.query(Incident).filter(Incident.detected_at >= this_month_start).all()
    previous = db.query(Incident).filter(
        Incident.detected_at >= last_month_start,
        Incident.detected_at < this_month_start,
    ).all()

    curr_count = len(current)
    prev_count = max(len(previous), 1)
    change = ((curr_count - prev_count) / prev_count) * 100

    return {
        "type": "monthly_trends",
        "current_month": curr_count,
        "previous_month": len(previous),
        "change_percent": round(change, 1),
        "trend": "increasing" if change > 10 else "decreasing" if change < -10 else "stable",
        "generated_at": now.isoformat(),
    }


@router.get("/executive")
def executive_summary(db: Session = Depends(get_db)):
    """Generate a non-technical executive summary."""
    month_ago = datetime.utcnow() - timedelta(days=30)
    monthly = db.query(Incident).filter(Incident.detected_at >= month_ago).all()
    resolved = [i for i in monthly if i.status == "resolved"]

    hours_saved = len(resolved) * 0.5
    cost_saved = hours_saved * 75

    return {
        "type": "executive_summary",
        "period": "Last 30 days",
        "stats": {
            "total_incidents": len(monthly),
            "auto_resolved": len(resolved),
            "hours_saved": round(hours_saved, 1),
            "cost_saved": round(cost_saved, 2),
            "uptime_percent": round(max(0, 100 - len(monthly) * 0.5), 1),
            "resolution_rate": round(len(resolved) / max(len(monthly), 1) * 100, 1),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


def _generate_postmortem_md(inc: dict) -> str:
    """Generate a markdown post-mortem from incident data."""
    return f"""# Post-Mortem: {inc.get('title', 'Incident')}

## Summary
| Field | Value |
|-------|-------|
| Service | {inc.get('service_name', 'N/A')} |
| Severity | {inc.get('severity', 'N/A')} |
| Detected | {inc.get('detected_at', 'N/A')} |
| Status | {inc.get('status', 'N/A')} |

## Description
{inc.get('description', 'No description.')}

## Root Cause
{inc.get('root_cause', 'Under investigation.')}

## Resolution
{inc.get('solution', 'Pending.')}

## Action Items
- [ ] Review monitoring for {inc.get('service_name', 'service')}
- [ ] Update runbooks
- [ ] Schedule review meeting
"""
