from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    service_name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    commit_hash = Column(String, nullable=True)
    deployed_by = Column(String, nullable=True)
    description = Column(String, nullable=True)
    deployed_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", backref="deployments")

    def __repr__(self):
        return f"<Deployment {self.service_name} v{self.version}>"
