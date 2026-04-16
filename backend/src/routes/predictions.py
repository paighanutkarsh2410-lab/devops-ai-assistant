"""API routes for predictions, forecasts, capacity planning, and costs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime

from models import get_db, PredictiveAlert, Forecast, CapacityPlan, CostForecast

router = APIRouter(prefix="/predictions", tags=["predictions"])


# ── Predictive Alerts ───────────────────────────────────────────────────

@router.get("/alerts")
def get_predictive_alerts(
    severity: Optional[str] = None,
    prevented: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get predictive alerts with filtering."""
    query = db.query(PredictiveAlert)
    if severity:
        query = query.filter(PredictiveAlert.severity == severity)
    if prevented is not None:
        query = query.filter(PredictiveAlert.prevented == prevented)
    return query.order_by(desc(PredictiveAlert.created_at)).limit(limit).all()


@router.post("/alerts")
def create_predictive_alert(data: dict, db: Session = Depends(get_db)):
    """Create a new predictive alert."""
    forecasted_date = None
    fd = data.get("forecasted_date")
    if fd:
        try:
            forecasted_date = datetime.fromisoformat(str(fd).replace("Z", ""))
        except (ValueError, TypeError):
            pass

    alert = PredictiveAlert(
        title=data.get("title", "Predicted Issue"),
        message=data.get("message", ""),
        severity=data.get("severity", "low"),
        prediction_type=data.get("prediction_type", "unknown"),
        service_name=data.get("service_name"),
        metric_name=data.get("metric_name"),
        confidence=data.get("confidence", 50),
        forecasted_date=forecasted_date,
        hours_until_issue=data.get("hours_until_issue") or data.get("hours_until_breach"),
        preventive_actions=data.get("preventive_actions"),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/alerts/{alert_id}/prevent")
def mark_alert_prevented(alert_id: str, data: dict, db: Session = Depends(get_db)):
    """Mark a predictive alert as prevented."""
    alert = db.query(PredictiveAlert).filter(PredictiveAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.prevented = True
    alert.prevention_action = data.get("action_taken", "manual")
    alert.prevented_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/alerts/stats")
def get_predictive_alert_stats(db: Session = Depends(get_db)):
    """Get stats about predictive alerts."""
    total = db.query(func.count(PredictiveAlert.id)).scalar() or 0
    prevented = db.query(func.count(PredictiveAlert.id)).filter(
        PredictiveAlert.prevented == True
    ).scalar() or 0

    by_type = db.query(
        PredictiveAlert.prediction_type,
        func.count().label("count"),
    ).group_by(PredictiveAlert.prediction_type).all()

    return {
        "total": total,
        "prevented": prevented,
        "prevention_rate": round(prevented / total * 100, 1) if total > 0 else 0,
        "active": total - prevented,
        "by_type": {row.prediction_type: row.count for row in by_type},
    }


# ── Forecasts ───────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metric_forecasts(
    service_name: Optional[str] = None,
    metric_name: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get stored metric forecasts."""
    query = db.query(Forecast).filter(Forecast.forecast_type == "metric")
    if service_name:
        query = query.filter(Forecast.service_name == service_name)
    if metric_name:
        query = query.filter(Forecast.metric_name == metric_name)
    return query.order_by(desc(Forecast.created_at)).limit(limit).all()


@router.post("/metrics")
def store_metric_forecast(data: dict, db: Session = Depends(get_db)):
    """Store a new metric forecast."""
    forecast = Forecast(
        service_name=data.get("service_name", ""),
        metric_name=data.get("metric_name", ""),
        forecast_type="metric",
        horizon_hours=data.get("horizon_hours", 24),
        method=data.get("method", "linear_regression"),
        forecast_data=data.get("forecast_data"),
        trend_direction=data.get("trend_direction"),
        breach_predicted=data.get("breach_predicted", False),
        hours_until_breach=data.get("hours_until_breach"),
        confidence=data.get("confidence", 50),
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast


# ── Capacity ────────────────────────────────────────────────────────────

@router.get("/capacity")
def get_capacity_plans(
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get capacity plans."""
    query = db.query(CapacityPlan)
    if status:
        query = query.filter(CapacityPlan.status == status)
    return query.order_by(desc(CapacityPlan.created_at)).limit(limit).all()


@router.post("/plan-event")
def create_event_plan(data: dict, db: Session = Depends(get_db)):
    """Create a capacity plan for an expected traffic event."""
    plan = CapacityPlan(
        service_name=data.get("service_name", "all"),
        plan_type="event",
        event_name=data.get("event_name", ""),
        current_utilization=data.get("current_utilization", 0),
        predicted_utilization=data.get("predicted_utilization", 0),
        recommendation=data.get("recommendation", ""),
        additional_instances=data.get("additional_instances", 0),
        estimated_cost=data.get("estimated_cost", 0),
        plan_data=data.get("plan_data"),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# ── Costs ───────────────────────────────────────────────────────────────

@router.get("/costs/current")
def get_current_costs(db: Session = Depends(get_db)):
    """Get the latest cost forecast."""
    latest = db.query(CostForecast).order_by(desc(CostForecast.created_at)).first()
    if not latest:
        return {"current_cost": 0, "predicted_cost": 0, "message": "No cost data yet"}
    return latest


@router.get("/costs/forecast")
def get_cost_forecast(limit: int = 6, db: Session = Depends(get_db)):
    """Get historical cost forecasts."""
    return db.query(CostForecast).order_by(desc(CostForecast.created_at)).limit(limit).all()


@router.get("/costs/optimization")
def get_cost_optimizations(db: Session = Depends(get_db)):
    """Get cost optimization recommendations from the latest forecast."""
    latest = db.query(CostForecast).order_by(desc(CostForecast.created_at)).first()
    if not latest or not latest.optimizations:
        return {"optimizations": [], "message": "No optimization data yet"}
    return {"optimizations": latest.optimizations}


# ── Trends ──────────────────────────────────────────────────────────────

@router.get("/trends")
def get_trend_forecasts(
    service_name: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get forecasts with trending direction."""
    query = db.query(Forecast).filter(
        Forecast.trend_direction.isnot(None)
    )
    if service_name:
        query = query.filter(Forecast.service_name == service_name)
    return query.order_by(desc(Forecast.created_at)).limit(limit).all()
