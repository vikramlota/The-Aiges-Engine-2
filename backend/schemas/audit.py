from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- Audit Schemas ---

class AuditCreate(BaseModel):
    platform: str
    content_type: str
    material_connection: str
    caption: str = ""
    influencer_handle: Optional[str] = ""
    post_url: Optional[str] = ""

    is_virtual_influencer: bool = False
    ai_disclosure_present_and_persistent: Optional[bool] = None
    makes_health_finance_or_technical_claim: bool = False
    credentials_or_substantiation_shown: Optional[bool] = None

    video_verbal_disclosure_second: Optional[int] = None
    video_overlay_covers_sponsored_segment: Optional[bool] = None
    story_label_superimposed: Optional[bool] = None

    ai_generated_or_enhanced: bool = False
    ai_content_label_present: Optional[bool] = None
    names_specific_competitor: bool = False
    unqualified_superiority_claim: Optional[bool] = None
    product_category: Optional[str] = None
    mandatory_disclaimer_present: Optional[bool] = None
    content_categories: List[str] = Field(default_factory=list)


class SimilarAudit(BaseModel):
    id: int
    caption: str
    status: str
    risk_level: Optional[str] = None
    similarity: float


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    risk_level: Optional[str] = None
    violations: List[str] = Field(default_factory=list)
    expert_review: List[str] = Field(default_factory=list)
    explanations: Dict[str, str] = Field(default_factory=dict)
    summary: str
    caption: str
    created_at: datetime
    similar_past_audits: List[SimilarAudit] = Field(default_factory=list)


class AuditListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caption: str
    status: str
    risk_level: Optional[str] = None
    created_at: datetime


# --- Pipeline & Link / Account Audit Schemas ---

class LinkAuditRequest(BaseModel):
    url: str
    ig_username: Optional[str] = None
    yt_api_key: Optional[str] = None
    ig_token: Optional[str] = None
    ig_account_id: Optional[str] = None
    enable_ai: bool = False
    ai_provider: str = "ollama"
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None


class LinkAuditResponse(BaseModel):
    id: Optional[int] = None
    platform: str
    influencer_handle: str
    post_url: str
    timestamp: str = ""
    caption: str = ""
    status: str
    risk_level: Optional[str] = None
    caption_flags: List[str] = Field(default_factory=list)
    visual_status: str = "NO_MEDIA"
    visual_flags: List[str] = Field(default_factory=list)
    is_compliant: bool = False
    ai_status: Optional[str] = None
    ai_explanation: Optional[str] = None
    ai_recommended_fix: Optional[str] = None
    ai_claims: List[str] = Field(default_factory=list)
    similar_past_audits: List[SimilarAudit] = Field(default_factory=list)


class AccountAuditRequest(BaseModel):
    account_url: str
    limit: int = Field(5, ge=1, le=15)
    yt_api_key: Optional[str] = None
    ig_token: Optional[str] = None
    ig_account_id: Optional[str] = None
    enable_ai: bool = False
    ai_provider: str = "ollama"
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None


class AccountPostSummary(BaseModel):
    post_id: str
    post_url: str
    timestamp: str = ""
    status: str
    risk_level: Optional[str] = None
    is_compliant: bool
    caption_flags: List[str] = Field(default_factory=list)
    visual_status: str
    visual_flags: List[str] = Field(default_factory=list)


class AccountAuditResponse(BaseModel):
    platform: str
    target_name: str
    total_audited: int
    compliant_count: int
    flagged_count: int
    expert_review_count: int
    health_score: float
    posts: List[AccountPostSummary] = Field(default_factory=list)
