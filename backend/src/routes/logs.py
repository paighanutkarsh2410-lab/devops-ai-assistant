import re
import logging
from collections import Counter
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from models import get_db
from models.user import User
from schemas.log import LogCreate, LogBulkCreate, LogResponse, ErrorPattern
from services.log_service import store_log, store_logs_bulk, fetch_logs, find_error_patterns
from utils.auth import get_current_user
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-memory analysis store
_analysis_store: List[Dict] = []

# Error patterns for smart classification
SMART_PATTERNS = [
    {"pattern": r"OutOfMemoryError|OOM|oom-killer", "category": "memory", "severity": "critical"},
    {"pattern": r"Connection refused|ECONNREFUSED|connection reset", "category": "connectivity", "severity": "high"},
    {"pattern": r"TimeoutError|timeout|timed out|deadline exceeded", "category": "timeout", "severity": "high"},
    {"pattern": r"disk full|no space left|ENOSPC", "category": "disk", "severity": "critical"},
    {"pattern": r"500 Internal Server Error|502 Bad Gateway|503 Service Unavailable", "category": "server_error", "severity": "high"},
    {"pattern": r"authentication failed|invalid token|jwt expired", "category": "auth", "severity": "medium"},
    {"pattern": r"deadlock|lock timeout", "category": "database", "severity": "critical"},
    {"pattern": r"segfault|segmentation fault|SIGSEGV", "category": "crash", "severity": "critical"},
    {"pattern": r"rate limit|throttl|429", "category": "rate_limit", "severity": "medium"},
    {"pattern": r"DNS|name resolution|NXDOMAIN", "category": "dns", "severity": "high"},
    {"pattern": r"SSL|TLS|certificate", "category": "ssl", "severity": "high"},
    {"pattern": r"CPU.*100%|cpu spike|high cpu", "category": "cpu", "severity": "high"},
]

RECS_MAP = {
    "memory": "Check for memory leaks, increase heap size, or add memory limits",
    "connectivity": "Verify service health, check network policies, review firewall rules",
    "timeout": "Increase timeout values, check downstream service latency",
    "disk": "Clean up old logs/temp files, increase volume size, set up log rotation",
    "database": "Check for long-running queries, review connection pool settings",
    "crash": "Review core dumps, check for null pointers, review recent deployments",
    "auth": "Check token expiry, verify credentials, review auth service health",
    "ssl": "Check certificate expiry, verify CA chain, update TLS configuration",
    "cpu": "Identify hot code paths, check for infinite loops, consider scaling",
    "rate_limit": "Implement backoff, review API quotas, consider caching",
    "dns": "Check DNS server health, verify domain configuration",
    "server_error": "Check application logs for stack traces, review recent deployments",
}


def _classify_message(message: str) -> Dict[str, str]:
    for ep in SMART_PATTERNS:
        if re.search(ep["pattern"], message, re.IGNORECASE):
            return {"category": ep["category"], "severity": ep["severity"]}
    return {"category": "general", "severity": "info"}

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/", response_model=LogResponse, status_code=201)
def create_log(
    data: LogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return store_log(db, current_user.id, data.service_name, data.level,
                     data.message, data.timestamp)


@router.post("/bulk", status_code=201)
def create_logs_bulk(
    data: LogBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = [
        {
            "user_id": current_user.id,
            "service_name": l.service_name,
            "level": l.level,
            "message": l.message,
            "timestamp": l.timestamp or datetime.utcnow()
        }
        for l in data.logs
    ]
    count = store_logs_bulk(db, logs)
    return {"inserted": count}


@router.get("/", response_model=List[LogResponse])
def list_logs(
    service_name: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    hours: int = Query(1, ge=1, le=168),
    limit: int = Query(200, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return fetch_logs(db, current_user.id, service_name, level, hours, limit)


@router.get("/errors", response_model=List[LogResponse])
def list_errors(
    service_name: Optional[str] = Query(None),
    hours: int = Query(1, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return fetch_logs(db, current_user.id, service_name, level="ERROR", hours=hours)


@router.get("/patterns", response_model=List[ErrorPattern])
def get_error_patterns(
    service_name: Optional[str] = Query(None),
    hours: int = Query(1, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return find_error_patterns(db, current_user.id, service_name, hours)


# ── Smart Log Analysis Endpoints ───────────────────────────────────────


class LogAnalyzeRequest(BaseModel):
    logs: List[Dict[str, Any]]


class LogAnalyzeResponse(BaseModel):
    total: int
    errors: int
    warnings: int
    patterns: List[Dict[str, Any]]
    recommendations: List[str]
    top_categories: Dict[str, int]


@router.post("/analyze", response_model=LogAnalyzeResponse)
def analyze_logs(
    data: LogAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze a batch of logs and return error patterns + recommendations."""
    errors = []
    warnings = []
    category_counts: Counter = Counter()
    patterns_found: List[Dict[str, Any]] = []

    for log in data.logs:
        message = log.get("message", "")
        level = log.get("level", "INFO").upper()

        classification = _classify_message(message)

        if level in ("ERROR", "FATAL", "CRITICAL"):
            errors.append({**log, **classification})
            category_counts[classification["category"]] += 1
        elif level in ("WARN", "WARNING"):
            warnings.append({**log, **classification})

    # Build pattern summary
    seen_categories = set()
    for err in errors:
        cat = err.get("category", "general")
        if cat not in seen_categories and cat != "general":
            seen_categories.add(cat)
            count = category_counts[cat]
            patterns_found.append({
                "category": cat,
                "severity": err.get("severity", "info"),
                "count": count,
                "sample": err.get("message", "")[:200],
            })

    patterns_found.sort(key=lambda p: p["count"], reverse=True)

    # Build recommendations
    recommendations = []
    for p in patterns_found[:5]:
        rec = RECS_MAP.get(p["category"])
        if rec:
            recommendations.append(f"{p['category']} ({p['count']}x): {rec}")

    return LogAnalyzeResponse(
        total=len(data.logs),
        errors=len(errors),
        warnings=len(warnings),
        patterns=patterns_found,
        recommendations=recommendations,
        top_categories=dict(category_counts.most_common(10)),
    )


@router.post("/analyze/store")
def store_analysis(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Store an AI-generated log analysis result."""
    entry = {
        "id": len(_analysis_store) + 1,
        "user_id": str(current_user.id),
        "analysis": data.get("analysis", ""),
        "clusters_analyzed": data.get("clusters_analyzed", 0),
        "total_errors": data.get("total_errors", 0),
        "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }
    _analysis_store.append(entry)
    return entry


@router.get("/analyze/history")
def get_analysis_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Get recent log analysis results."""
    user_analyses = [a for a in _analysis_store if a.get("user_id") == str(current_user.id)]
    return {"analyses": user_analyses[-limit:], "total": len(user_analyses)}


@router.get("/stats")
def get_log_stats(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get log statistics summary."""
    all_logs = fetch_logs(db, current_user.id, service_name=None, level=None, hours=hours, limit=2000)

    level_counts: Counter = Counter()
    service_counts: Counter = Counter()
    category_counts: Counter = Counter()

    for log in all_logs:
        level_counts[log.level] += 1
        service_counts[log.service_name] += 1
        classification = _classify_message(log.message)
        if classification["category"] != "general":
            category_counts[classification["category"]] += 1

    return {
        "total_logs": len(all_logs),
        "hours": hours,
        "by_level": dict(level_counts.most_common()),
        "by_service": dict(service_counts.most_common(10)),
        "error_categories": dict(category_counts.most_common(10)),
        "smart_patterns_available": len(SMART_PATTERNS),
    }
