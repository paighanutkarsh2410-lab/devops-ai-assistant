"""Full-text search and advanced filtering for incidents."""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, cast, String
from datetime import datetime
from models.incident import Incident
from models.incident_comment import IncidentComment
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Full-text search across incidents, comments, and diagnostics."""

    def __init__(self, db: Session):
        self.db = db

    def search_incidents(
        self,
        user_id: str,
        query: str = None,
        status: list[str] = None,
        severity: list[str] = None,
        service_name: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        auto_resolved: bool = None,
        sort_by: str = "detected_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """Search incidents with full-text and advanced filters."""
        q = self.db.query(Incident).filter(Incident.user_id == user_id)

        # Full-text search across multiple fields
        if query:
            search_term = f"%{query}%"
            q = q.filter(or_(
                Incident.title.ilike(search_term),
                Incident.description.ilike(search_term),
                Incident.root_cause.ilike(search_term),
                Incident.solution.ilike(search_term),
                Incident.service_name.ilike(search_term),
            ))

        # Status filter (multi-select)
        if status:
            q = q.filter(Incident.status.in_(status))

        # Severity filter (multi-select)
        if severity:
            q = q.filter(Incident.severity.in_(severity))

        # Service filter
        if service_name:
            q = q.filter(Incident.service_name == service_name)

        # Date range
        if date_from:
            q = q.filter(Incident.detected_at >= date_from)
        if date_to:
            q = q.filter(Incident.detected_at <= date_to)

        # Auto-resolved filter
        if auto_resolved is not None:
            q = q.filter(Incident.auto_resolved == auto_resolved)

        # Count total before pagination
        total = q.count()

        # Sorting
        sort_col = getattr(Incident, sort_by, Incident.detected_at)
        if sort_order == "asc":
            q = q.order_by(sort_col.asc())
        else:
            q = q.order_by(sort_col.desc())

        # Pagination
        results = q.offset(skip).limit(limit).all()

        return {
            "results": results,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total,
        }

    def get_search_suggestions(self, user_id: str, partial: str) -> dict:
        """Return autocomplete suggestions as user types."""
        suggestions = {"services": [], "severities": [], "statuses": []}

        if partial:
            term = f"%{partial}%"
            # Service names
            services = (
                self.db.query(Incident.service_name)
                .filter(Incident.user_id == user_id, Incident.service_name.ilike(term))
                .distinct()
                .limit(5)
                .all()
            )
            suggestions["services"] = [s[0] for s in services if s[0]]

        # Always return available filter options
        suggestions["severities"] = ["critical", "high", "medium", "low"]
        suggestions["statuses"] = ["open", "investigating", "resolved", "closed"]

        return suggestions

    def export_incidents(self, user_id: str, format: str = "json", **filters) -> list[dict]:
        """Export filtered incidents for CSV/JSON download."""
        result = self.search_incidents(user_id, limit=10000, **filters)
        incidents = result["results"]
        return [
            {
                "id": str(i.id),
                "title": i.title,
                "severity": i.severity,
                "status": i.status,
                "service_name": i.service_name,
                "root_cause": i.root_cause,
                "solution": i.solution,
                "detected_at": i.detected_at.isoformat() if i.detected_at else None,
                "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
                "auto_resolved": i.auto_resolved,
            }
            for i in incidents
        ]
