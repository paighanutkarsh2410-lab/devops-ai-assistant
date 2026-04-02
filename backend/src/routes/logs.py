from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import get_db
from models.user import User
from schemas.log import LogCreate, LogBulkCreate, LogResponse, ErrorPattern
from services.log_service import store_log, store_logs_bulk, fetch_logs, find_error_patterns
from utils.auth import get_current_user
from datetime import datetime

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
