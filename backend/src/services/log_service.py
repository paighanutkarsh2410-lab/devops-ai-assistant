"""Log analysis service: fetch, parse, and find error patterns."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.log_entry import LogEntry
from datetime import datetime, timedelta
from typing import List, Optional
from collections import Counter
import re


def store_log(db: Session, user_id, service_name: str, level: str,
              message: str, timestamp: datetime = None, metadata: dict = None) -> LogEntry:
    entry = LogEntry(
        user_id=user_id,
        service_name=service_name,
        level=level,
        message=message,
        timestamp=timestamp or datetime.utcnow(),
        extra_data=metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def store_logs_bulk(db: Session, logs: List[dict]) -> int:
    objects = [LogEntry(**l) for l in logs]
    db.add_all(objects)
    db.commit()
    return len(objects)


def fetch_logs(db: Session, user_id, service_name: Optional[str] = None,
               level: Optional[str] = None, hours: int = 1,
               limit: int = 200) -> List[LogEntry]:
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(LogEntry).filter(
        LogEntry.user_id == user_id,
        LogEntry.timestamp >= since
    )
    if service_name:
        query = query.filter(LogEntry.service_name == service_name)
    if level:
        query = query.filter(LogEntry.level == level)
    return query.order_by(LogEntry.timestamp.desc()).limit(limit).all()


def get_logs_around_time(db: Session, user_id, service_name: str,
                         timestamp: datetime, window_minutes: int = 5) -> List[LogEntry]:
    """Get logs within a time window around a specific timestamp."""
    start = timestamp - timedelta(minutes=window_minutes)
    end = timestamp + timedelta(minutes=window_minutes)
    return db.query(LogEntry).filter(
        LogEntry.user_id == user_id,
        LogEntry.service_name == service_name,
        LogEntry.timestamp.between(start, end)
    ).order_by(LogEntry.timestamp).all()


def find_error_patterns(db: Session, user_id, service_name: Optional[str] = None,
                        hours: int = 1) -> List[dict]:
    """Group similar error messages and count occurrences."""
    logs = fetch_logs(db, user_id, service_name, level="ERROR", hours=hours, limit=500)

    # Normalize messages for grouping
    patterns = Counter()
    for log in logs:
        normalized = _normalize_message(log.message)
        patterns[normalized] += 1

    return [
        {"pattern": pattern, "count": count, "level": "ERROR"}
        for pattern, count in patterns.most_common(20)
    ]


def _normalize_message(message: str) -> str:
    """Normalize log message for pattern matching (remove IDs, timestamps, IPs)."""
    msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', message)
    msg = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', msg)
    msg = re.sub(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\b', '<TIMESTAMP>', msg)
    msg = re.sub(r'\b\d{4,}\b', '<NUM>', msg)
    return msg.strip()
