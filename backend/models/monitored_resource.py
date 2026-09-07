from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import utc_now

class MonitoredResource(Base):
    __tablename__ = "monitored_resources"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    platform = Column(String, default="Instagram", nullable=False)
    resource_id = Column(String, nullable=False, index=True)  # e.g., post_id
    
    last_scraped_at = Column(DateTime, nullable=True)
    status = Column(String, default="active", nullable=False)  # active, paused, error
    created_at = Column(DateTime, default=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
