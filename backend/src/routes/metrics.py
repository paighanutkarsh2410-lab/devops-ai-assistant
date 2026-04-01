from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import get_db
from models.user import User
from schemas.metric import MetricCreate, MetricBulkCreate, MetricResponse, MetricAggregation
from services.metric_service import store_metric, store_metrics_bulk, get_metrics, get_metric_aggregations
from utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/", response_model=MetricResponse, status_code=201)
def create_metric(
    data: MetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store a single metric."""
    return store_metric(
        db, current_user.id, data.service_name, data.metric_name,
        data.value, data.unit, data.timestamp
    )


@router.post("/bulk", status_code=201)
def create_metrics_bulk(
    data: MetricBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store multiple metrics at once."""
    metrics = [
        {
            "user_id": current_user.id,
            "service_name": m.service_name,
            "metric_name": m.metric_name,
            "value": m.value,
            "unit": m.unit,
            "timestamp": m.timestamp or datetime.utcnow()
        }
        for m in data.metrics
    ]
    count = store_metrics_bulk(db, metrics)
    return {"inserted": count}


@router.get("/", response_model=List[MetricResponse])
def list_metrics(
    service_name: Optional[str] = Query(None),
    metric_name: Optional[str] = Query(None),
    hours: int = Query(1, ge=1, le=168),
    limit: int = Query(500, ge=1, le=5000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics within a time range."""
    return get_metrics(db, current_user.id, service_name, metric_name, hours, limit)


@router.get("/aggregations", response_model=MetricAggregation)
def get_aggregations(
    service_name: str = Query(...),
    metric_name: str = Query(...),
    hours: int = Query(1, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get aggregated metric values (avg, min, max)."""
    return get_metric_aggregations(db, current_user.id, service_name, metric_name, hours)
