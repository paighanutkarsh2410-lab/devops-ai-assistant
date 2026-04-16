from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid
from datetime import datetime, timezone


class CustomAgent(Base):
    __tablename__ = "custom_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    enabled = Column(Boolean, default=True)

    # Trigger configuration
    triggers = Column(JSON, default=dict)
    # Data sources to analyze
    data_sources = Column(JSON, default=list)
    # LLM prompt template
    analysis_prompt = Column(Text, default="")
    # Actions to execute
    actions = Column(JSON, default=list)
    # Full config blob
    config = Column(JSON, default=dict)

    # Template info
    template_id = Column(String(100), nullable=True)

    # Stats
    total_runs = Column(String, default="0")
    last_run_at = Column(DateTime, nullable=True)
    last_result = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
