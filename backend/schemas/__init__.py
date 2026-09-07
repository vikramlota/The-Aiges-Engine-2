# Re-export all schemas across domain modules for convenient top-level import
from backend.schemas.common import (
    MaterialConnectionItem,
    ExpertReviewCategoryItem,
    MetaResponse,
)
from backend.schemas.user import (
    UserSignup,
    UserResponse,
    Token,
)
from backend.schemas.audit import (
    AuditCreate,
    SimilarAudit,
    AuditResponse,
    AuditListItem,
    LinkAuditRequest,
    LinkAuditResponse,
    AccountAuditRequest,
    AccountPostSummary,
    AccountAuditResponse,
)
from backend.schemas.mention import (
    CommentItem,
    MentionIngestRequest,
    MentionResponse,
    DailySentimentTrend,
    AnomalyReport,
    MentionSummaryResponse,
    RetentionCleanupRequest,
    RetentionCleanupResponse,
    DraftReplyRequest,
    DraftReplyResponse,
    ApproveReplyRequest,
    ApproveReplyResponse,
)
from backend.schemas.campaign import (
    AdChannelBase,
    AdChannelCreate,
    AdChannelResponse,
    CampaignCreate,
    CampaignResponse,
    ChannelShift,
    AllocationRecommendationResponse,
    ApproveRecommendationRequest,
)
from backend.schemas.monitored_resource import (
    MonitoredResourceCreate,
    MonitoredResourceResponse,
)

__all__ = [
    # Common / Meta
    "MaterialConnectionItem",
    "ExpertReviewCategoryItem",
    "MetaResponse",
    # User / Auth
    "UserSignup",
    "UserResponse",
    "Token",
    # Audit
    "AuditCreate",
    "SimilarAudit",
    "AuditResponse",
    "AuditListItem",
    "LinkAuditRequest",
    "LinkAuditResponse",
    "AccountAuditRequest",
    "AccountPostSummary",
    "AccountAuditResponse",
    # Mention
    "CommentItem",
    "MentionIngestRequest",
    "MentionResponse",
    "DailySentimentTrend",
    "AnomalyReport",
    "MentionSummaryResponse",
    "RetentionCleanupRequest",
    "RetentionCleanupResponse",
    "DraftReplyRequest",
    "DraftReplyResponse",
    "ApproveReplyRequest",
    "ApproveReplyResponse",
    # Campaign / Ad Allocation
    "AdChannelBase",
    "AdChannelCreate",
    "AdChannelResponse",
    "CampaignCreate",
    "CampaignResponse",
    "ChannelShift",
    "AllocationRecommendationResponse",
    "ApproveRecommendationRequest",
    
    # Monitored Resource
    "MonitoredResourceCreate",
    "MonitoredResourceResponse",
]
