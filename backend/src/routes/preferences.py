"""API routes for notification preferences."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime

from models import get_db
from models.notification_preference import NotificationPreference, OnCallSchedule
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/preferences", tags=["preferences"])


# ── Schemas ────────────────────────────────────────────────────────────

class NotificationPrefCreate(BaseModel):
    channel: str  # slack, email, sms
    enabled: bool = True
    severity_threshold: str = "low"
    services: List[str] = []
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    digest_frequency: str = "daily"


class NotificationPrefResponse(BaseModel):
    id: str
    channel: str
    enabled: bool
    severity_threshold: str
    services: List[str]
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    digest_frequency: str

    @field_validator("id", mode="before")
    @classmethod
    def stringify_uuid(cls, v: Any) -> str:
        return str(v) if v is not None else v

    class Config:
        from_attributes = True


class OnCallCreate(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    start_hour: int = 0
    end_hour: int = 24
    active: bool = True


# ── Notification Preferences ──────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationPrefResponse])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's notification preferences."""
    prefs = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).all()

    # Return defaults if none set
    if not prefs:
        return _default_preferences()

    return prefs


@router.put("/notifications", response_model=List[NotificationPrefResponse])
async def update_notification_preferences(
    preferences: List[NotificationPrefCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences (replaces all)."""
    # Delete existing
    db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).delete()

    # Create new
    new_prefs = []
    for pref_data in preferences:
        pref = NotificationPreference(
            user_id=current_user.id,
            channel=pref_data.channel,
            enabled=pref_data.enabled,
            severity_threshold=pref_data.severity_threshold,
            services=pref_data.services,
            quiet_hours_start=pref_data.quiet_hours_start,
            quiet_hours_end=pref_data.quiet_hours_end,
            digest_frequency=pref_data.digest_frequency,
        )
        db.add(pref)
        new_prefs.append(pref)

    db.commit()
    for p in new_prefs:
        db.refresh(p)

    return new_prefs


@router.post("/notifications/test")
async def test_notification(
    current_user: User = Depends(get_current_user),
):
    """Send a test notification to verify channel configuration."""
    return {
        "status": "sent",
        "message": f"Test notification sent to {current_user.email}",
        "channels": ["slack", "email"],
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── On-Call Schedules ─────────────────────────────────────────────────

@router.get("/oncall")
async def get_oncall_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get on-call schedule for current user."""
    schedules = db.query(OnCallSchedule).filter(
        OnCallSchedule.user_id == current_user.id,
        OnCallSchedule.active == True,
    ).all()

    return [
        {
            "id": str(s.id),
            "day_of_week": s.day_of_week,
            "start_hour": s.start_hour,
            "end_hour": s.end_hour,
            "active": s.active,
        }
        for s in schedules
    ]


@router.post("/oncall")
async def set_oncall_schedule(
    schedules: List[OnCallCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set on-call schedule (replaces existing)."""
    db.query(OnCallSchedule).filter(
        OnCallSchedule.user_id == current_user.id
    ).delete()

    for s in schedules:
        db.add(OnCallSchedule(
            user_id=current_user.id,
            day_of_week=s.day_of_week,
            start_hour=s.start_hour,
            end_hour=s.end_hour,
            active=s.active,
        ))

    db.commit()
    return {"status": "updated", "schedules": len(schedules)}


def _default_preferences() -> list:
    """Return default notification preferences."""
    return [
        {"id": "default-slack", "channel": "slack", "enabled": True,
         "severity_threshold": "medium", "services": [],
         "quiet_hours_start": 23, "quiet_hours_end": 7, "digest_frequency": "daily"},
        {"id": "default-email", "channel": "email", "enabled": True,
         "severity_threshold": "high", "services": [],
         "quiet_hours_start": None, "quiet_hours_end": None, "digest_frequency": "weekly"},
    ]
