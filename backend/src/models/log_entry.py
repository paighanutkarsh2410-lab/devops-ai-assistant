from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    service_name = Column(String, nullable=False, index=True)
    level = Column(String, nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    extra_data = Column("metadata", JSON, nullable=True)

    user = relationship("User", backref="log_entries")

    __table_args__ = (
        Index('ix_logs_service_time', 'service_name', 'timestamp'),
        Index('ix_logs_level_time', 'level', 'timestamp'),
    )

    def __repr__(self):
        return f"<Log [{self.level}] {self.service_name}: {self.message[:50]}>"
