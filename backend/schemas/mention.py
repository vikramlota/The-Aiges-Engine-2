from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- Phase 2.1: Mention & Sentiment Schemas ---

class CommentItem(BaseModel):
    text: str
    author_handle: Optional[str] = ""
    detected_at: Optional[datetime] = None


class MentionIngestRequest(BaseModel):
    post_id: str
    platform: str = "Instagram"
    author_handle: Optional[str] = ""
    comments: Optional[List[CommentItem]] = None
    ig_token: Optional[str] = None
    ig_account_id: Optional[str] = None
    ig_username: Optional[str] = None


class MentionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    post_id: str
    platform: str
    author_handle: str
    text: str
    sentiment: str
    sentiment_score: float
    detected_at: datetime
    flagged_for_review: bool
    explanation: str
    language: str = "en"

    # Phase 2.2 fields
    drafted_reply: Optional[str] = None
    draft_explanation: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


class DailySentimentTrend(BaseModel):
    date: str
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    needs_review: int = 0
    flagged: int = 0


class AnomalyReport(BaseModel):
    is_anomalous: bool
    current_daily_negative: int
    trailing_7day_avg: float
    threshold: float
    explanation: str


class MentionSummaryResponse(BaseModel):
    total_mentions: int
    positive_count: int
    neutral_count: int
    negative_count: int
    needs_review_count: int = 0
    flagged_count: int
    positive_rate: float
    negative_rate: float
    daily_trend: List[DailySentimentTrend] = Field(default_factory=list)
    anomaly: AnomalyReport


class RetentionCleanupRequest(BaseModel):
    days_retention: int = Field(90, ge=7, le=365)


class RetentionCleanupResponse(BaseModel):
    deleted_count: int
    retention_days: int
    status: str = "COMPLETED"


# --- Phase 2.2: Response-Drafting Agent Schemas ---

class DraftReplyRequest(BaseModel):
    custom_instructions: Optional[str] = None
    brand_name: Optional[str] = "Our Brand"
    provider: Optional[str] = "ollama"
    model_name: Optional[str] = None
    api_key: Optional[str] = None


class DraftReplyResponse(BaseModel):
    mention_id: int
    drafted_reply: str
    draft_explanation: str


class ApproveReplyRequest(BaseModel):
    edited_reply: Optional[str] = None


class ApproveReplyResponse(BaseModel):
    mention_id: int
    drafted_reply: str
    approved_by: int
    approved_at: datetime
    status: str = "APPROVED"
