from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    audits = relationship("AuditRecord", back_populates="owner", cascade="all, delete-orphan")
    mentions = relationship("Mention", back_populates="owner", foreign_keys="[Mention.owner_id]", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="owner", cascade="all, delete-orphan")
