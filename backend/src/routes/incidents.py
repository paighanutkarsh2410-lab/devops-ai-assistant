from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import get_db
from models.user import User
from models.incident import Incident
from schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate
from schemas.timeline import TimelineResponse, TimelineEvent
from services.timeline_service import generate_timeline
from services.llm_service import generate_timeline_summary
from utils.auth import get_current_user
from services.search_service import SearchService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_data: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new incident"""

    new_incident = Incident(
        user_id=current_user.id,
        title=incident_data.title,
        description=incident_data.description,
        severity=incident_data.severity,
        service_name=incident_data.service_name,
        status="open"
    )

    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    return new_incident


@router.get("/", response_model=List[IncidentResponse])
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all incidents for current user"""

    query = db.query(Incident).filter(Incident.user_id == current_user.id)

    if status:
        query = query.filter(Incident.status == status)

    incidents = query.order_by(Incident.detected_at.desc()).offset(skip).limit(limit).all()

    return incidents


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific incident"""

    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: str,
    update_data: IncidentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an incident"""

    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Update fields
    if update_data.status:
        incident.status = update_data.status
    if update_data.root_cause:
        incident.root_cause = update_data.root_cause
    if update_data.solution:
        incident.solution = update_data.solution
    if update_data.resolved_at:
        incident.resolved_at = update_data.resolved_at

        # Calculate resolution time
        time_diff = incident.resolved_at - incident.detected_at
        incident.resolution_time_seconds = int(time_diff.total_seconds())

    db.commit()
    db.refresh(incident)

    return incident


@router.get("/{incident_id}/timeline", response_model=TimelineResponse)
def get_incident_timeline(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chronological timeline of events for an incident."""
    events = generate_timeline(db, incident_id, current_user.id)
    if not events:
        raise HTTPException(status_code=404, detail="Incident not found")

    summary = None
    if len(events) >= 2:
        try:
            summary = generate_timeline_summary(events)
        except Exception:
            summary = None

    return TimelineResponse(
        incident_id=incident_id,
        events=[TimelineEvent(**e) for e in events],
        summary=summary
    )


@router.get("/search/results")
def search_incidents(
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    service_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    auto_resolved: Optional[bool] = None,
    sort_by: str = "detected_at",
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Advanced search with full-text and filters."""
    from datetime import datetime as dt
    svc = SearchService(db)
    result = svc.search_incidents(
        user_id=str(current_user.id),
        query=q,
        status=status_filter.split(",") if status_filter else None,
        severity=severity.split(",") if severity else None,
        service_name=service_name,
        date_from=dt.fromisoformat(date_from) if date_from else None,
        date_to=dt.fromisoformat(date_to) if date_to else None,
        auto_resolved=auto_resolved,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )
    return {
        "results": [IncidentResponse.model_validate(i) for i in result["results"]],
        "total": result["total"],
        "has_more": result["has_more"],
    }


@router.get("/search/suggestions")
def search_suggestions(
    q: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Autocomplete suggestions for search."""
    svc = SearchService(db)
    return svc.get_search_suggestions(str(current_user.id), q)


@router.get("/export")
def export_incidents(
    format: str = "json",
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export incidents as JSON (CSV available via frontend)."""
    svc = SearchService(db)
    data = svc.export_incidents(
        user_id=str(current_user.id),
        status=status_filter.split(",") if status_filter else None,
        severity=severity.split(",") if severity else None,
    )
    return {"format": format, "count": len(data), "data": data}


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an incident"""

    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    db.delete(incident)
    db.commit()

    return None
