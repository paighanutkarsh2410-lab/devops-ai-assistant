from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid
from datetime import datetime, timezone


class MarketplaceItem(Base):
    __tablename__ = "marketplace_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    item_type = Column(String(50), nullable=False)  # agent, plugin, workflow, dashboard, report
    category = Column(String(50), default="general")
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    author_name = Column(String(100), default="Community")
    version = Column(String(20), default="1.0.0")

    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    price = Column(String(20), default="free")
    verified = Column(Boolean, default=False)

    config_template = Column(JSON, default=dict)
    installation_instructions = Column(Text, default="")
    tags = Column(JSON, default=list)
    screenshots = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    changelog = Column(JSON, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class MarketplaceReview(Base):
    __tablename__ = "marketplace_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    changelog = Column(Text, default="")
    release_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    performance_baseline = Column(JSON, default=dict)
    status = Column(String(20), default="active")  # active, deprecated, beta
    config = Column(JSON, default=dict)


class AgentMetrics(Base):
    __tablename__ = "agent_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    metric_metadata = Column("metadata", JSON, default=dict)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
