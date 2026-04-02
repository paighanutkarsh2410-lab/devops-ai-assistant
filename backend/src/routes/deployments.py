from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import get_db
from models.user import User
from models.deployment import Deployment
from schemas.deployment import DeploymentCreate, DeploymentResponse
from utils.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("/", response_model=DeploymentResponse, status_code=201)
def create_deployment(
    data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dep = Deployment(
        user_id=current_user.id,
        service_name=data.service_name,
        version=data.version,
        commit_hash=data.commit_hash,
        deployed_by=data.deployed_by,
        description=data.description,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.get("/", response_model=List[DeploymentResponse])
def list_deployments(
    service_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Deployment).filter(Deployment.user_id == current_user.id)
    if service_name:
        query = query.filter(Deployment.service_name == service_name)
    return query.order_by(Deployment.deployed_at.desc()).limit(limit).all()


@router.get("/recent", response_model=List[DeploymentResponse])
def list_recent_deployments(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(hours=hours)
    return db.query(Deployment).filter(
        Deployment.user_id == current_user.id,
        Deployment.deployed_at >= since
    ).order_by(Deployment.deployed_at.desc()).all()
