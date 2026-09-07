from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import utc_now


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    total_monthly_budget = Column(Float, default=100000.0, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    owner = relationship("User", back_populates="campaigns")
    channels = relationship("AdChannel", back_populates="campaign", cascade="all, delete-orphan")
    recommendations = relationship("AllocationRecommendation", back_populates="campaign", cascade="all, delete-orphan")


class AdChannel(Base):
    __tablename__ = "ad_channels"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    current_allocation_pct = Column(Float, default=25.0, nullable=False)
    current_spend = Column(Float, default=0.0, nullable=False)
    impressions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    revenue = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, nullable=False)

    campaign = relationship("Campaign", back_populates="channels")


class AllocationRecommendation(Base):
    __tablename__ = "allocation_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)

    # JSON text storing channel shift deltas, target percentages, and target spends
    recommended_shifts = Column(Text, default="{}", nullable=False)
    reasoning = Column(Text, default="", nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)

    # Auditable human-approval fields
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING", nullable=False)   # PENDING | APPROVED | REJECTED
    created_at = Column(DateTime, default=utc_now, nullable=False)

    campaign = relationship("Campaign", back_populates="recommendations")
    approver = relationship("User", foreign_keys=[approved_by])
