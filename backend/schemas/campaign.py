from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- Phase 2.3: Ad-Allocation & Bandit Optimizer Schemas ---

class AdChannelBase(BaseModel):
    name: str
    current_allocation_pct: float = 25.0
    current_spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0


class AdChannelCreate(AdChannelBase):
    pass


class AdChannelResponse(AdChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    updated_at: datetime


class CampaignCreate(BaseModel):
    name: str
    total_monthly_budget: float = 100000.0
    currency: str = "INR"
    channels: Optional[List[AdChannelCreate]] = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    total_monthly_budget: float
    currency: str
    created_at: datetime
    channels: List[AdChannelResponse] = Field(default_factory=list)


class ChannelShift(BaseModel):
    channel_name: str
    current_pct: float
    suggested_pct: float
    delta_pct: float
    current_spend: float
    suggested_spend: float
    roas: float
    conversions: int
    win_probability: float


class AllocationRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    shifts: List[ChannelShift] = Field(default_factory=list)
    reasoning: str
    confidence: float
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    status: str
    created_at: datetime


class ApproveRecommendationRequest(BaseModel):
    notes: Optional[str] = None
