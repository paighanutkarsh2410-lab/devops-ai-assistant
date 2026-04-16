"""API routes for learning data, patterns, action outcomes, and recommendations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, Integer
from typing import Optional
from datetime import datetime

from models import get_db, LearningData, ActionOutcome, Pattern, Incident
from schemas.learning import (
    LearningDataCreate, LearningDataResponse,
    ActionOutcomeCreate, ActionOutcomeResponse,
    PatternResponse,
    RecommendationRequest,
)

router = APIRouter(prefix="/learning", tags=["learning"])


# ── Learning Data ───────────────────────────────────────────────────────

@router.post("/data", response_model=LearningDataResponse)
def upsert_learning_data(data: LearningDataCreate, db: Session = Depends(get_db)):
    """Create or update learning data for a pattern+action combo."""
    # Find existing entry
    existing = db.query(LearningData).filter(
        LearningData.pattern_type == data.pattern_type,
        LearningData.action_name == data.action_name,
    ).first()

    if existing:
        existing.frequency += 1
        existing.total_attempts += 1
        if data.success:
            existing.total_successes += 1
        existing.success_rate = (
            existing.total_successes / existing.total_attempts * 100
            if existing.total_attempts > 0 else 0
        )
        existing.confidence = min(existing.success_rate, 95)
        existing.last_seen = datetime.utcnow()
        if data.symptoms:
            existing.symptoms = data.symptoms
        if data.service_name:
            existing.service_name = data.service_name
        db.commit()
        db.refresh(existing)
        return existing

    entry = LearningData(
        pattern_type=data.pattern_type,
        action_name=data.action_name,
        service_name=data.service_name,
        frequency=1,
        total_attempts=1,
        total_successes=1 if data.success else 0,
        success_rate=100.0 if data.success else 0.0,
        confidence=50.0,
        symptoms=data.symptoms,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/data")
def get_learning_data(
    pattern_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get learning data entries."""
    query = db.query(LearningData)
    if pattern_type:
        query = query.filter(LearningData.pattern_type == pattern_type)
    return query.order_by(desc(LearningData.frequency)).limit(limit).all()


# ── Action Outcomes ─────────────────────────────────────────────────────

@router.post("/outcomes", response_model=ActionOutcomeResponse)
def record_outcome(data: ActionOutcomeCreate, db: Session = Depends(get_db)):
    """Record an action outcome for tracking."""
    outcome = ActionOutcome(
        incident_id=data.incident_id,
        action_name=data.action_name,
        incident_pattern=data.incident_pattern,
        service_name=data.service_name,
        success=data.success,
        duration_seconds=data.duration_seconds,
        impact_score=data.impact_score,
        was_recommended=data.was_recommended,
        recommendation_rank=data.recommendation_rank,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


@router.get("/outcomes")
def get_outcomes(
    action_name: Optional[str] = None,
    pattern: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get action outcomes with optional filtering."""
    query = db.query(ActionOutcome)
    if action_name:
        query = query.filter(ActionOutcome.action_name == action_name)
    if pattern:
        query = query.filter(ActionOutcome.incident_pattern == pattern)
    return query.order_by(desc(ActionOutcome.timestamp)).limit(limit).all()


@router.get("/outcomes/stats")
def get_outcome_stats(db: Session = Depends(get_db)):
    """Get aggregate stats for action outcomes."""
    rows = db.query(
        ActionOutcome.action_name,
        func.count().label("total"),
        func.count().filter(ActionOutcome.success == True).label("successes"),
        func.avg(ActionOutcome.duration_seconds).label("avg_duration"),
        func.avg(ActionOutcome.impact_score).label("avg_impact"),
    ).group_by(ActionOutcome.action_name).all()

    stats = []
    for row in rows:
        total = row.total or 0
        successes = int(row.successes or 0)
        stats.append({
            "action_name": row.action_name,
            "total": total,
            "successes": successes,
            "success_rate": round(successes / total * 100, 1) if total > 0 else 0,
            "avg_duration": round(float(row.avg_duration or 0), 2),
            "avg_impact": round(float(row.avg_impact or 0), 2),
        })

    return sorted(stats, key=lambda x: x["total"], reverse=True)


# ── Patterns ────────────────────────────────────────────────────────────

@router.get("/patterns")
def get_patterns(
    trending: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get discovered incident patterns."""
    query = db.query(Pattern)
    if trending:
        query = query.filter(Pattern.trending == trending)
    return query.order_by(desc(Pattern.frequency)).limit(limit).all()


@router.post("/patterns")
def upsert_pattern(data: dict, db: Session = Depends(get_db)):
    """Create or update a discovered pattern."""
    existing = db.query(Pattern).filter(
        Pattern.pattern_type == data.get("pattern_type", "")
    ).first()

    if existing:
        existing.frequency = data.get("frequency", existing.frequency)
        existing.confidence = data.get("confidence", existing.confidence)
        existing.trending = data.get("trending", existing.trending)
        existing.last_seen = datetime.utcnow()
        if data.get("symptoms"):
            existing.symptoms = data["symptoms"]
        if data.get("common_root_causes"):
            existing.common_root_causes = data["common_root_causes"]
        if data.get("best_actions"):
            existing.best_actions = data["best_actions"]
        if data.get("affected_services"):
            existing.affected_services = data["affected_services"]
        db.commit()
        db.refresh(existing)
        return existing

    pattern = Pattern(
        name=data.get("name", data.get("pattern_type", "Unknown")),
        description=data.get("description", ""),
        pattern_type=data.get("pattern_type", "unknown"),
        frequency=data.get("frequency", 1),
        confidence=data.get("confidence", 0),
        symptoms=data.get("symptoms"),
        common_root_causes=data.get("common_root_causes"),
        best_actions=data.get("best_actions"),
        affected_services=data.get("affected_services"),
        trending=data.get("trending", "stable"),
    )
    db.add(pattern)
    db.commit()
    db.refresh(pattern)
    return pattern


# ── Learning Stats ──────────────────────────────────────────────────────

@router.get("/stats")
def get_learning_stats(db: Session = Depends(get_db)):
    """Get overall learning system statistics."""
    total_patterns = db.query(func.count(Pattern.id)).scalar() or 0
    total_outcomes = db.query(func.count(ActionOutcome.id)).scalar() or 0
    total_learning = db.query(func.count(LearningData.id)).scalar() or 0

    successful_outcomes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.success == True
    ).scalar() or 0

    avg_resolution = db.query(func.avg(ActionOutcome.duration_seconds)).filter(
        ActionOutcome.success == True
    ).scalar() or 0

    recommended_outcomes = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.was_recommended == True
    ).scalar() or 0

    recommended_success = db.query(func.count(ActionOutcome.id)).filter(
        ActionOutcome.was_recommended == True,
        ActionOutcome.success == True,
    ).scalar() or 0

    # Most effective action
    best_action_row = db.query(
        LearningData.action_name,
        LearningData.success_rate,
    ).filter(
        LearningData.total_attempts >= 3,
    ).order_by(desc(LearningData.success_rate)).first()

    return {
        "total_patterns_discovered": total_patterns,
        "total_outcomes_tracked": total_outcomes,
        "total_learning_entries": total_learning,
        "overall_success_rate": round(
            successful_outcomes / total_outcomes * 100, 1
        ) if total_outcomes > 0 else 0,
        "avg_resolution_time_seconds": round(float(avg_resolution), 2),
        "recommendation_accuracy": round(
            recommended_success / recommended_outcomes * 100, 1
        ) if recommended_outcomes > 0 else 0,
        "most_effective_action": best_action_row.action_name if best_action_row else None,
        "knowledge_base_hit_rate": 0,  # Updated by learning agent
    }


# ── Recommendations ─────────────────────────────────────────────────────

@router.post("/recommend")
def recommend_actions(req: RecommendationRequest, db: Session = Depends(get_db)):
    """Recommend best actions for an incident based on historical data."""
    incident = db.query(Incident).filter(Incident.id == req.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get learning data for this pattern type
    root_cause = (incident.root_cause or "").lower()
    service = incident.service_name or ""

    # Find matching learning data entries
    entries = db.query(LearningData).filter(
        LearningData.total_attempts >= 1,
    ).order_by(desc(LearningData.success_rate)).limit(20).all()

    recommendations = []
    for entry in entries:
        if not entry.action_name:
            continue

        # Basic relevance check
        relevance = 0.5
        if entry.service_name == service:
            relevance += 0.2
        if entry.pattern_type and entry.pattern_type in root_cause:
            relevance += 0.3

        confidence = min(
            entry.success_rate * 0.6 + relevance * 40,
            99,
        )

        recommendations.append({
            "action_name": entry.action_name,
            "confidence": round(confidence, 1),
            "success_rate": round(entry.success_rate, 1),
            "similar_count": entry.total_attempts,
            "avg_similarity": round(relevance, 3),
            "explanation": (
                f"This action has a {entry.success_rate:.0f}% success rate "
                f"across {entry.total_attempts} attempts for {entry.pattern_type} patterns."
            ),
        })

    recommendations.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "incident_id": str(incident.id),
        "recommendations": recommendations[:5],
        "similar_incidents": [],
    }
