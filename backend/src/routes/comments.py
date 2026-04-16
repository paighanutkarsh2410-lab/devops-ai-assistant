"""Incident comments and assignments API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime
from models import get_db
from models.user import User
from models.incident_comment import IncidentComment
from models.incident_assignment import IncidentAssignment
from utils.auth import get_current_user

router = APIRouter(tags=["collaboration"])


# ── Schemas ─────────────────────────────────────────────────

class CommentCreate(BaseModel):
    comment_text: str
    attachments: Optional[list] = None

class CommentResponse(BaseModel):
    id: str
    incident_id: str
    user_id: str
    comment_text: str
    attachments: Optional[list] = None
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_validator("id", "incident_id", "user_id", mode="before")
    @classmethod
    def stringify_uuid(cls, v: Any) -> str:
        return str(v) if v is not None else v

class AssignmentCreate(BaseModel):
    user_id: str

class AssignmentResponse(BaseModel):
    id: str
    incident_id: str
    user_id: str
    status: str
    assigned_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_validator("id", "incident_id", "user_id", mode="before")
    @classmethod
    def stringify_uuid(cls, v: Any) -> str:
        return str(v) if v is not None else v


# ── Comments ────────────────────────────────────────────────

@router.post("/incidents/{incident_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    incident_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = IncidentComment(
        incident_id=incident_id,
        user_id=current_user.id,
        comment_text=data.comment_text,
        attachments=data.attachments,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/incidents/{incident_id}/comments", response_model=List[CommentResponse])
def list_comments(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(IncidentComment)
        .filter(IncidentComment.incident_id == incident_id)
        .order_by(IncidentComment.created_at.asc())
        .all()
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(IncidentComment).filter(
        IncidentComment.id == comment_id,
        IncidentComment.user_id == current_user.id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.comment_text = data.comment_text
    comment.edited_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(IncidentComment).filter(
        IncidentComment.id == comment_id,
        IncidentComment.user_id == current_user.id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
    return {"deleted": True}


# ── Assignments ─────────────────────────────────────────────

@router.post("/incidents/{incident_id}/assign", response_model=AssignmentResponse, status_code=201)
def assign_incident(
    incident_id: str,
    data: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = IncidentAssignment(
        incident_id=incident_id,
        user_id=data.user_id,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/incidents/{incident_id}/assignments", response_model=List[AssignmentResponse])
def list_assignments(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(IncidentAssignment)
        .filter(IncidentAssignment.incident_id == incident_id)
        .all()
    )
