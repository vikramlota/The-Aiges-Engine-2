from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import utc_now


class Mention(Base):
    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    post_id = Column(String, nullable=False, index=True)
    platform = Column(String, default="Instagram", nullable=False)
    author_handle = Column(String, default="", nullable=False)
    text = Column(Text, nullable=False)

    sentiment = Column(String, nullable=False)          # "positive" | "negative" | "neutral"
    sentiment_score = Column(Float, nullable=False)      # -1.0 to 1.0
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    flagged_for_review = Column(Boolean, default=False, nullable=False)
    explanation = Column(Text, default="", nullable=False)
    language = Column(String, default="en", nullable=False)

    # Phase 2.2: Response-Drafting & Human-Approval Fields
    drafted_reply = Column(Text, nullable=True)
    draft_explanation = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="mentions")
    approver = relationship("User", foreign_keys=[approved_by])
