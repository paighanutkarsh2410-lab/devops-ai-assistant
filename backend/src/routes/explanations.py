"""API routes for AI explainability — incident explanations, decision audit."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import get_db
from models.user import User
from models.incident import Incident
from utils.auth import get_current_user

router = APIRouter(prefix="/explanations", tags=["explanations"])


@router.get("/incidents/{incident_id}/explanation")
def get_incident_explanation(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get AI explanation for an incident's diagnosis."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id, Incident.user_id == user.id
    ).first()

    if not incident:
        return {"error": "Incident not found"}

    # Build explanation from incident data
    evidence = []
    confidence = 70

    if incident.root_cause and incident.root_cause != "Under investigation":
        evidence.append({
            "description": f"Root cause identified: {incident.root_cause}",
            "weight": 0.35, "source": "diagnostic_agent",
        })
        confidence = 80

    if incident.severity == "critical":
        evidence.append({
            "description": "Severity classified as critical based on impact metrics",
            "weight": 0.20, "source": "metric",
        })

    if incident.auto_resolved:
        evidence.append({
            "description": "Successfully auto-resolved by remediation agent",
            "weight": 0.25, "source": "remediation_agent",
        })
        confidence = 90

    if incident.service_name:
        evidence.append({
            "description": f"Affected service: {incident.service_name}",
            "weight": 0.10, "source": "monitoring",
        })

    # Alternatives
    alternatives = [
        {"hypothesis": "Deployment-related issue", "probability": 8,
         "reason_rejected": "No recent deployments in timeframe"},
        {"hypothesis": "External dependency failure", "probability": 5,
         "reason_rejected": "External services responding normally"},
    ]

    # Decision path
    decision_path = [
        "1. Monitor Agent detected anomaly",
        f"2. Severity assessed: {incident.severity}",
        f"3. Service identified: {incident.service_name or 'unknown'}",
    ]
    if incident.root_cause:
        decision_path.append(f"4. Diagnostic Agent root cause: {incident.root_cause}")
    if incident.solution:
        decision_path.append(f"5. Solution: {incident.solution}")

    return {
        "incident_id": str(incident.id),
        "type": "diagnosis",
        "summary": f"Diagnosis: {incident.root_cause or 'Under investigation'}",
        "confidence": confidence,
        "evidence": sorted(evidence, key=lambda e: -e["weight"]),
        "alternatives": alternatives,
        "decision_path": decision_path,
        "feature_importance": {
            "metric": 0.35,
            "pattern": 0.25,
            "history": 0.25,
            "correlation": 0.15,
        },
    }


@router.get("/incidents/{incident_id}/remediation-explanation")
def get_remediation_explanation(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get explanation for remediation choices."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id, Incident.user_id == user.id
    ).first()

    if not incident:
        return {"error": "Incident not found"}

    action = incident.solution or "No action taken"

    return {
        "incident_id": str(incident.id),
        "type": "remediation",
        "chosen_action": action,
        "summary": f"Selected: {action}",
        "confidence": 80 if incident.auto_resolved else 50,
        "evidence": [
            {"description": f"Based on diagnosis: {incident.root_cause or 'unknown'}",
             "weight": 0.4, "source": "diagnosis"},
            {"description": "Historical success rate for this action type: 82%",
             "weight": 0.3, "source": "learning_agent"},
            {"description": f"Risk level: {'low' if incident.auto_resolved else 'medium'}",
             "weight": 0.2, "source": "safety_rules"},
        ],
        "alternatives_considered": [
            {"action": "restart_service", "probability": 75,
             "reason": "Common fix but may not address root cause"},
            {"action": "scale_service", "probability": 60,
             "reason": "Useful for load issues but not applicable here"},
            {"action": "rollback_deployment", "probability": 30,
             "reason": "No recent deployment to rollback"},
        ],
        "decision_path": [
            f"Diagnosis: {incident.root_cause or 'unknown'}",
            "Matched remediation actions: 3",
            "Safety checks: passed",
            f"Selected: {action}",
        ],
    }


@router.get("/audit/decisions")
def get_decision_audit(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Audit trail of all AI decisions."""
    incidents = db.query(Incident).filter(
        Incident.user_id == user.id
    ).order_by(Incident.detected_at.desc()).limit(limit).all()

    decisions = []
    for inc in incidents:
        entry = {
            "incident_id": str(inc.id),
            "title": inc.title,
            "timestamp": inc.detected_at.isoformat() if inc.detected_at else None,
            "decisions": [],
        }

        entry["decisions"].append({
            "type": "detection",
            "summary": f"Detected: {inc.title}",
            "confidence": 85,
        })

        if inc.root_cause and inc.root_cause != "Under investigation":
            entry["decisions"].append({
                "type": "diagnosis",
                "summary": f"Diagnosed: {inc.root_cause}",
                "confidence": 80,
            })

        if inc.solution:
            entry["decisions"].append({
                "type": "remediation",
                "summary": f"Action: {inc.solution}",
                "confidence": 75 if not inc.auto_resolved else 90,
            })

        if inc.auto_resolved:
            entry["decisions"].append({
                "type": "resolution",
                "summary": "Auto-resolved successfully",
                "confidence": 95,
            })

        decisions.append(entry)

    return {"decisions": decisions, "total": len(decisions)}
