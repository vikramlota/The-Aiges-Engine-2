import os
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import User, Mention, MonitoredResource, utc_now
from backend.schemas import (
    MentionIngestRequest,
    MentionResponse,
    MentionSummaryResponse,
    DailySentimentTrend,
    AnomalyReport,
    DraftReplyRequest,
    DraftReplyResponse,
    ApproveReplyRequest,
    ApproveReplyResponse,
    RetentionCleanupRequest,
    RetentionCleanupResponse,
    MonitoredResourceCreate,
    MonitoredResourceResponse,
)
from backend.auth import get_current_user
from backend.sentiment import analyze_comment
from backend.response_agent import draft_response_for_mention

router = APIRouter(prefix="/api/mentions", tags=["Mentions & Reputation"])


@router.post("/ingest", response_model=List[MentionResponse], status_code=status.HTTP_201_CREATED)
def ingest_mentions(
    req: MentionIngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ingests comments for an Instagram post, scores sentiment with offline VADER lexicon,
    detects brand crisis keywords, and saves to the user's reputation tracking database.
    """
    post_id = req.post_id.strip()
    if not post_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="post_id cannot be empty.")

    comments_to_process = []

    # 1. Direct comment payload (for manual submission, testing, or offline agencies)
    if req.comments and len(req.comments) > 0:
        for c in req.comments:
            if c.text and c.text.strip():
                comments_to_process.append({
                    "text": c.text.strip(),
                    "author_handle": c.author_handle or req.author_handle or "@anonymous",
                    "detected_at": c.detected_at or utc_now()
                })

    # 2. Instagram Graph API (Business Discovery) comment retrieval
    else:
        username = req.ig_username
        token = req.ig_token or os.getenv("IG_ACCESS_TOKEN")
        account_id = req.ig_account_id or os.getenv("IG_ACCOUNT_ID")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instagram comments ingestion requires 'ig_username' (or provide direct 'comments' list)."
            )
        if not token or not account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meta API Access Token and Business Account ID are required for live Instagram comment fetching."
            )

        api_url = f"https://graph.facebook.com/v25.0/{account_id}"
        fields = f"business_discovery.username({username}){{media{{id,caption,comments{{id,text,timestamp,username}}}}}}"
        params = {"fields": fields, "access_token": token}

        max_retries = 3
        data = None
        for attempt in range(max_retries):
            try:
                resp = requests.get(api_url, params=params, timeout=10)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Instagram comment ingestion failed: {str(e)}"
                    )
                time.sleep(1)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve comment data from Instagram Graph API."
            )

        media_list = data.get("business_discovery", {}).get("media", {}).get("data", [])

        for m in media_list:
            if m.get("id") == post_id:
                # Rate limit & volume protection: Cap batch comment fetching to max 50 comments
                raw_comment_list = m.get("comments", {}).get("data", [])[:50]
                for raw_comment in raw_comment_list:
                    raw_time = raw_comment.get("timestamp")
                    parsed_time = None
                    if raw_time:
                        try:
                            parsed_time = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                        except Exception:
                            parsed_time = utc_now()

                    comments_to_process.append({
                        "text": raw_comment.get("text", "").strip(),
                        "author_handle": f"@{raw_comment.get('username', 'user')}",
                        "detected_at": parsed_time or utc_now()
                    })
                break

    if not comments_to_process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comments were provided or found for this post ID."
        )

    # 3. Analyze sentiment and store mentions
    saved_mentions = []
    for item in comments_to_process:
        analysis = analyze_comment(item["text"])

        mention = Mention(
            owner_id=current_user.id,
            post_id=post_id,
            platform=req.platform,
            author_handle=item["author_handle"],
            text=item["text"],
            sentiment=analysis["sentiment"],
            sentiment_score=analysis["sentiment_score"],
            detected_at=item["detected_at"],
            flagged_for_review=analysis["flagged_for_review"],
            explanation=analysis["explanation"],
            language=analysis.get("language", "en")
        )
        db.add(mention)
        saved_mentions.append(mention)

    db.commit()
    for m in saved_mentions:
        db.refresh(m)

    return saved_mentions


@router.get("", response_model=List[MentionResponse])
def get_mentions(
    sentiment: Optional[str] = Query(None, description="Filter by positive, negative, neutral, or needs_review"),
    language: Optional[str] = Query(None, description="Filter by language: en, hinglish, indic"),
    flagged_only: bool = Query(False, description="Filter only flagged mentions"),
    post_id: Optional[str] = Query(None, description="Filter by post ID"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List mentions for the authenticated user, filterable by sentiment, flagged status, or post ID.
    """
    query = db.query(Mention).filter(Mention.owner_id == current_user.id)

    if sentiment:
        query = query.filter(Mention.sentiment == sentiment.lower().strip())
    if language:
        query = query.filter(Mention.language == language.lower().strip())
    if flagged_only:
        query = query.filter(Mention.flagged_for_review == True)
    if post_id:
        query = query.filter(Mention.post_id == post_id.strip())

    mentions = query.order_by(Mention.detected_at.desc()).offset(skip).limit(limit).all()
    return mentions


@router.get("/summary", response_model=MentionSummaryResponse)
def get_mentions_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns aggregate sentiment metrics, daily trend, and statistical anomaly detection:
    Flags when daily negative sentiment volume exceeds roughly 2x the trailing 7-day average.
    """
    all_user_mentions = (
        db.query(Mention)
        .filter(Mention.owner_id == current_user.id)
        .order_by(Mention.detected_at.asc())
        .all()
    )

    total_count = len(all_user_mentions)
    positive_count = sum(1 for m in all_user_mentions if m.sentiment == "positive")
    neutral_count = sum(1 for m in all_user_mentions if m.sentiment == "neutral")
    negative_count = sum(1 for m in all_user_mentions if m.sentiment == "negative")
    needs_review_count = sum(1 for m in all_user_mentions if m.sentiment == "needs_review")
    flagged_count = sum(1 for m in all_user_mentions if m.flagged_for_review)

    pos_rate = round((positive_count / total_count) * 100, 1) if total_count > 0 else 0.0
    neg_rate = round((negative_count / total_count) * 100, 1) if total_count > 0 else 0.0

    # Build daily trend
    daily_buckets: Dict[str, Dict[str, int]] = {}
    for m in all_user_mentions:
        date_str = m.detected_at.strftime("%Y-%m-%d")
        if date_str not in daily_buckets:
            daily_buckets[date_str] = {"positive": 0, "neutral": 0, "negative": 0, "needs_review": 0, "flagged": 0}
        if m.sentiment in daily_buckets[date_str]:
            daily_buckets[date_str][m.sentiment] += 1
        else:
            daily_buckets[date_str][m.sentiment] = 1
        if m.flagged_for_review:
            daily_buckets[date_str]["flagged"] += 1

    daily_trend = [
        DailySentimentTrend(
            date=d,
            positive=counts.get("positive", 0),
            neutral=counts.get("neutral", 0),
            negative=counts.get("negative", 0),
            needs_review=counts.get("needs_review", 0),
            flagged=counts.get("flagged", 0),
        )
        for d, counts in sorted(daily_buckets.items())
    ]

    # --- Anomaly Detection: Daily negative volume vs 2x trailing 7-day average ---
    # Determine reference date: most recent date in data, or today
    if daily_trend:
        ref_date = datetime.strptime(daily_trend[-1].date, "%Y-%m-%d").date()
        current_daily_negative = daily_buckets.get(ref_date.strftime("%Y-%m-%d"), {}).get("negative", 0)
    else:
        ref_date = datetime.now(timezone.utc).date()
        current_daily_negative = 0

    trailing_7_days = [ref_date - timedelta(days=i) for i in range(1, 8)]
    trailing_negative_sum = sum(
        daily_buckets.get(d.strftime("%Y-%m-%d"), {}).get("negative", 0)
        for d in trailing_7_days
    )
    trailing_7day_avg = round(trailing_negative_sum / 7.0, 2)
    threshold = round(max(2.0 * trailing_7day_avg, 2.0), 2)  # minimum threshold of 2.0

    # Statistical spike condition: current negative volume >= 3 and >= 2x trailing avg
    is_anomalous = (current_daily_negative >= 3) and (current_daily_negative >= 2.0 * trailing_7day_avg)

    if is_anomalous:
        anomaly_explanation = (
            f"Reputation Alert: Daily negative comment volume ({current_daily_negative}) "
            f"exceeded 2x the trailing 7-day average ({trailing_7day_avg:.1f}/day, threshold {threshold}). "
            f"Possible brand crisis or consumer backlash."
        )
    elif total_count == 0:
        anomaly_explanation = "No comment mentions tracked yet."
    else:
        anomaly_explanation = (
            f"Negative sentiment within normal statistical variance ({current_daily_negative} today vs "
            f"trailing 7-day average of {trailing_7day_avg}/day)."
        )

    anomaly = AnomalyReport(
        is_anomalous=is_anomalous,
        current_daily_negative=current_daily_negative,
        trailing_7day_avg=trailing_7day_avg,
        threshold=threshold,
        explanation=anomaly_explanation
    )

    return MentionSummaryResponse(
        total_mentions=total_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        needs_review_count=needs_review_count,
        flagged_count=flagged_count,
        positive_rate=pos_rate,
        negative_rate=neg_rate,
        daily_trend=daily_trend,
        anomaly=anomaly
    )


@router.post("/cleanup", response_model=RetentionCleanupResponse)
def cleanup_mentions(
    req: RetentionCleanupRequest = RetentionCleanupRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Data Privacy & Retention Enforcement (DPDP Act compliance):
    Deletes mention comments older than the specified retention window (default: 90 days).
    Enforces privacy by design and avoids unnecessary data accumulation.
    """
    cutoff_date = utc_now() - timedelta(days=req.days_retention)

    deleted_count = (
        db.query(Mention)
        .filter(Mention.owner_id == current_user.id, Mention.detected_at < cutoff_date)
        .delete(synchronize_session=False)
    )
    db.commit()

    return RetentionCleanupResponse(
        deleted_count=deleted_count,
        retention_days=req.days_retention,
        status="COMPLETED"
    )


@router.post("/{mention_id}/draft-reply", response_model=DraftReplyResponse)
def create_draft_reply(
    mention_id: int,
    req: DraftReplyRequest = DraftReplyRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Drafts an authentic, empathetic brand response to a negative or flagged comment.
    Does NOT post the reply or mark it as approved (maintaining strict human-approval separation).
    """
    mention = db.query(Mention).filter(Mention.id == mention_id, Mention.owner_id == current_user.id).first()
    if not mention:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mention not found.")

    draft_result = draft_response_for_mention(
        comment_text=mention.text,
        author_handle=mention.author_handle,
        sentiment=mention.sentiment,
        sentiment_score=mention.sentiment_score,
        crisis_explanation=mention.explanation,
        brand_name=req.brand_name or "Our Brand",
        custom_instructions=req.custom_instructions,
        provider=req.provider or "ollama",
        model_name=req.model_name,
        api_key=req.api_key
    )

    mention.drafted_reply = draft_result["drafted_reply"]
    mention.draft_explanation = draft_result["draft_explanation"]
    # Explicitly ensure approved_at is NOT set here
    db.commit()
    db.refresh(mention)

    return DraftReplyResponse(
        mention_id=mention.id,
        drafted_reply=mention.drafted_reply,
        draft_explanation=mention.draft_explanation
    )


@router.post("/{mention_id}/approve", response_model=ApproveReplyResponse)
def approve_reply(
    mention_id: int,
    req: ApproveReplyRequest = ApproveReplyRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Explicit human sign-off action on a drafted reply.
    Records approved_by and approved_at timestamp.
    """
    mention = db.query(Mention).filter(Mention.id == mention_id, Mention.owner_id == current_user.id).first()
    if not mention:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mention not found.")

    if not mention.drafted_reply and not req.edited_reply:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No draft reply exists for this mention. Generate a draft first or provide an edited reply."
        )

    if req.edited_reply and req.edited_reply.strip():
        mention.drafted_reply = req.edited_reply.strip()

    mention.approved_by = current_user.id
    mention.approved_at = utc_now()

    db.commit()
    db.refresh(mention)

    return ApproveReplyResponse(
        mention_id=mention.id,
        drafted_reply=mention.drafted_reply,
        approved_by=mention.approved_by,
        approved_at=mention.approved_at,
        status="APPROVED"
    )

# --- Phase 2.5: Automated Ingestion Management ---

@router.post("/monitor", response_model=MonitoredResourceResponse, status_code=status.HTTP_201_CREATED)
def add_monitored_resource(
    req: MonitoredResourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adds a new Instagram/YouTube resource to be automatically polled."""
    existing = db.query(MonitoredResource).filter(
        MonitoredResource.owner_id == current_user.id,
        MonitoredResource.platform == req.platform,
        MonitoredResource.resource_id == req.resource_id
    ).first()
    if existing:
        return existing
        
    resource = MonitoredResource(
        owner_id=current_user.id,
        platform=req.platform,
        resource_id=req.resource_id
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@router.get("/monitor", response_model=List[MonitoredResourceResponse])
def list_monitored_resources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all active automated polling resources for the user."""
    return db.query(MonitoredResource).filter(MonitoredResource.owner_id == current_user.id).all()

@router.delete("/monitor/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitored_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stops auto-polling and removes the monitored resource."""
    resource = db.query(MonitoredResource).filter(
        MonitoredResource.id == resource_id,
        MonitoredResource.owner_id == current_user.id
    ).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(resource)
    db.commit()

