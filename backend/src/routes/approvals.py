"""Approval request routes for human-in-the-loop remediation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models.database import get_db
from models.approval_request import ApprovalRequest
from schemas.approval import ApprovalCreate, ApprovalResponse, ApprovalAction
from routes.auth import get_current_user

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/", response_model=ApprovalResponse)
def create_approval(req: ApprovalCreate, db: Session = Depends(get_db)):
    """Create an approval request for a remediation action."""
    approval = ApprovalRequest(
        incident_id=req.incident_id,
        action_name=req.action_name,
        action_description=req.action_description,
        risk_level=req.risk_level,
        requested_by="RemediationAgent",
        status="pending",
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/", response_model=list[ApprovalResponse])
def list_approvals(status: str = None, limit: int = 20, db: Session = Depends(get_db)):
    """List approval requests, optionally filtered by status."""
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status)

    # Auto-expire old pending requests
    expiry_cutoff = datetime.utcnow() - timedelta(minutes=30)
    expired = db.query(ApprovalRequest).filter(
        ApprovalRequest.status == "pending",
        ApprovalRequest.requested_at < expiry_cutoff
    ).all()
    for a in expired:
        a.status = "expired"
    if expired:
        db.commit()

    return query.order_by(ApprovalRequest.requested_at.desc()).limit(limit).all()


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: str, db: Session = Depends(get_db)):
    """Get a specific approval request."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_action(approval_id: str, body: ApprovalAction = None,
                   db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    """Approve a pending remediation action."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve: status is {approval.status}")

    approval.status = "approved"
    approval.approved_by = current_user.id if hasattr(current_user, 'id') else str(current_user)
    approval.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject_action(approval_id: str, body: ApprovalAction = None,
                  db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    """Reject a pending remediation action."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot reject: status is {approval.status}")

    approval.status = "rejected"
    approval.approved_by = current_user.id if hasattr(current_user, 'id') else str(current_user)
    approval.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(approval)
    return approval
