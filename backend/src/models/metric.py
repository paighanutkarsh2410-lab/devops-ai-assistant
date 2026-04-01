from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Metric info
    service_name = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False, index=True)  # cpu, memory, disk, etc.
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)  # %, GB, ms, etc.

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="metrics")

    # Composite index for fast queries
    __table_args__ = (
        Index('ix_metrics_service_time', 'service_name', 'timestamp'),
        Index('ix_metrics_name_time', 'metric_name', 'timestamp'),
    )

    def __repr__(self):
        return f"<Metric {self.service_name}.{self.metric_name}={self.value}>"
