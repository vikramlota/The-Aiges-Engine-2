from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import utc_now


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    platform = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    material_connection = Column(String, nullable=False)
    caption = Column(Text, default="", nullable=False)
    influencer_handle = Column(String, default="")
    post_url = Column(String, default="")

    status = Column(String, nullable=False)
    risk_level = Column(String, nullable=True)

    # Stored as JSON strings
    violations = Column(Text, default="[]", nullable=False)
    expert_review = Column(Text, default="[]", nullable=False)
    explanations = Column(Text, default="{}", nullable=False)

    summary = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    owner = relationship("User", back_populates="audits")


# Alias for structurise.md recommendation
Audit = AuditRecord
