"""API routes for custom report builder — templates, generation, scheduling."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from models import get_db
from models.user import User
from models.report_template import ReportTemplate
from utils.auth import get_current_user
from analytics.analytics_engine import AnalyticsEngine

router = APIRouter(prefix="/report-builder", tags=["report-builder"])


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: str = "custom"
    widgets: list = []
    filters: Optional[dict] = None
    schedule: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[list] = None
    filters: Optional[dict] = None
    schedule: Optional[str] = None


# ── CRUD for templates ──────────────────────────────────────────────────

@router.get("/templates")
def list_templates(
    report_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ReportTemplate).filter(ReportTemplate.user_id == user.id)
    if report_type:
        q = q.filter(ReportTemplate.report_type == report_type)
    templates = q.order_by(ReportTemplate.updated_at.desc()).all()
    return [_serialize(t) for t in templates]


@router.post("/templates", status_code=201)
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tpl = ReportTemplate(
        user_id=user.id,
        name=body.name,
        description=body.description,
        report_type=body.report_type,
        widgets=body.widgets,
        filters=body.filters,
        schedule=body.schedule,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return _serialize(tpl)


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tpl = _get_owned(db, user, template_id)
    return _serialize(tpl)


@router.patch("/templates/{template_id}")
def update_template(
    template_id: str,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tpl = _get_owned(db, user, template_id)
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(tpl, field, val)
    tpl.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tpl)
    return _serialize(tpl)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tpl = _get_owned(db, user, template_id)
    db.delete(tpl)
    db.commit()


# ── Generate report from template ──────────────────────────────────────

@router.post("/templates/{template_id}/generate")
def generate_report(
    template_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Execute all widgets in a template and return assembled report data."""
    tpl = _get_owned(db, user, template_id)
    engine = AnalyticsEngine(db, str(user.id))
    date_from = datetime.utcnow() - timedelta(days=days)

    widget_results = []
    for w in (tpl.widgets or []):
        wtype = w.get("type", "")
        result = _execute_widget(engine, wtype, date_from, w.get("config", {}))
        widget_results.append({"widget": w, "data": result})

    return {
        "template_id": str(tpl.id),
        "template_name": tpl.name,
        "generated_at": datetime.utcnow().isoformat(),
        "period_days": days,
        "widgets": widget_results,
    }


# ── Preset templates ────────────────────────────────────────────────────

@router.get("/presets")
def list_presets():
    """Return built-in report presets users can clone."""
    return [
        {
            "name": "Operations Overview",
            "report_type": "operational",
            "widgets": [
                {"type": "mttr", "title": "Mean Time To Resolve", "size": "half"},
                {"type": "mttd", "title": "Mean Time To Detect", "size": "half"},
                {"type": "frequency", "title": "Incident Frequency", "size": "full"},
                {"type": "root_causes", "title": "Root Cause Distribution", "size": "half"},
                {"type": "reliability", "title": "Service Reliability", "size": "half"},
            ],
        },
        {
            "name": "Executive Summary",
            "report_type": "executive",
            "widgets": [
                {"type": "effectiveness", "title": "Automation Effectiveness", "size": "full"},
                {"type": "cost_impact", "title": "Cost Savings", "size": "half"},
                {"type": "frequency", "title": "Incident Trends", "size": "half"},
            ],
        },
        {
            "name": "Service Health",
            "report_type": "operational",
            "widgets": [
                {"type": "reliability", "title": "Reliability Scores", "size": "full"},
                {"type": "mttr", "title": "Resolution Times", "size": "half"},
                {"type": "root_causes", "title": "Failure Modes", "size": "half"},
            ],
        },
    ]


# ── Helpers ─────────────────────────────────────────────────────────────

def _get_owned(db: Session, user: User, template_id: str) -> ReportTemplate:
    tpl = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id, ReportTemplate.user_id == user.id
    ).first()
    if not tpl:
        raise HTTPException(404, "Template not found")
    return tpl


def _serialize(tpl: ReportTemplate) -> dict:
    return {
        "id": str(tpl.id),
        "name": tpl.name,
        "description": tpl.description,
        "report_type": tpl.report_type,
        "widgets": tpl.widgets,
        "filters": tpl.filters,
        "schedule": tpl.schedule,
        "created_at": tpl.created_at.isoformat() if tpl.created_at else None,
        "updated_at": tpl.updated_at.isoformat() if tpl.updated_at else None,
    }


def _execute_widget(engine: AnalyticsEngine, wtype: str, date_from, config: dict) -> dict:
    """Run an analytics query for a widget type."""
    try:
        if wtype == "mttr":
            return engine.calculate_mttr(date_from=date_from, filters=config)
        elif wtype == "mttd":
            return engine.calculate_mttd(date_from=date_from)
        elif wtype == "frequency":
            return engine.incident_frequency_analysis()
        elif wtype == "root_causes":
            return engine.root_cause_distribution()
        elif wtype == "reliability":
            return engine.service_reliability_score(config.get("service_name"))
        elif wtype == "effectiveness":
            return engine.effectiveness_metrics()
        elif wtype == "cost_impact":
            return engine.cost_impact_analysis()
        elif wtype == "blast_radius":
            inc_id = config.get("incident_id")
            if inc_id:
                return engine.calculate_blast_radius(inc_id)
            return {"error": "No incident_id in config"}
        else:
            return {"error": f"Unknown widget type: {wtype}"}
    except Exception as e:
        return {"error": str(e)}
