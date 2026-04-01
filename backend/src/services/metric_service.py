from sqlalchemy.orm import Session
from sqlalchemy import func
from models.metric import Metric
from datetime import datetime, timedelta
from typing import List, Optional


def store_metric(db: Session, user_id, service_name: str, metric_name: str,
                 value: float, unit: str = None, timestamp: datetime = None) -> Metric:
    """Store a single metric in the database."""
    metric = Metric(
        user_id=user_id,
        service_name=service_name,
        metric_name=metric_name,
        value=value,
        unit=unit,
        timestamp=timestamp or datetime.utcnow()
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def store_metrics_bulk(db: Session, metrics: List[dict]) -> int:
    """Store multiple metrics at once for performance."""
    objects = [Metric(**m) for m in metrics]
    db.add_all(objects)
    db.commit()
    return len(objects)


def get_metrics(db: Session, user_id, service_name: Optional[str] = None,
                metric_name: Optional[str] = None, hours: int = 1,
                limit: int = 500) -> List[Metric]:
    """Get metrics within a time range."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(Metric).filter(
        Metric.user_id == user_id,
        Metric.timestamp >= since
    )
    if service_name:
        query = query.filter(Metric.service_name == service_name)
    if metric_name:
        query = query.filter(Metric.metric_name == metric_name)

    return query.order_by(Metric.timestamp.desc()).limit(limit).all()


def get_metric_aggregations(db: Session, user_id, service_name: str,
                            metric_name: str, hours: int = 1) -> dict:
    """Get aggregated metric values (avg, min, max, count)."""
    since = datetime.utcnow() - timedelta(hours=hours)
    result = db.query(
        func.avg(Metric.value).label("avg"),
        func.min(Metric.value).label("min"),
        func.max(Metric.value).label("max"),
        func.count(Metric.id).label("count")
    ).filter(
        Metric.user_id == user_id,
        Metric.service_name == service_name,
        Metric.metric_name == metric_name,
        Metric.timestamp >= since
    ).first()

    return {
        "avg": float(result.avg) if result.avg else 0,
        "min": float(result.min) if result.min else 0,
        "max": float(result.max) if result.max else 0,
        "count": result.count or 0
    }
