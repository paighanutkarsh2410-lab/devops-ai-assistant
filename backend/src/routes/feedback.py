"""Feedback collection endpoint."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])

_feedback_store: list = []


class FeedbackSubmission(BaseModel):
    type: str = "general"
    message: str
    email: Optional[str] = None


@router.post("/feedback")
def submit_feedback(data: FeedbackSubmission):
    """Collect user feedback."""
    entry = {
        "type": data.type,
        "message": data.message,
        "email": data.email,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    _feedback_store.append(entry)
    logger.info(f"Feedback received: {data.type} — {data.message[:80]}")
    return {"status": "received", "id": len(_feedback_store)}


@router.get("/feedback")
def list_feedback():
    """List collected feedback."""
    return {"feedback": list(reversed(_feedback_store)), "total": len(_feedback_store)}
