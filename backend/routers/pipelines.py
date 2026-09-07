import os
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, AuditRecord
from backend.schemas import (
    LinkAuditRequest,
    LinkAuditResponse,
    AccountAuditRequest,
    AccountAuditResponse,
    AccountPostSummary,
    SimilarAudit
)
from backend.auth import get_current_user
from backend.vector_store import index_audit, find_similar_audits

# Ingestion pipeline imports
from pipelines.yt_pipeline import (
    extract_youtube_video_id,
    extract_youtube_channel_info,
    fetch_single_yt_video,
    run_yt_pipeline
)
from pipelines.ig_pipeline import (
    extract_instagram_info,
    fetch_single_ig_post,
    run_integrated_pipeline
)

router = APIRouter(prefix="/api/audits", tags=["Pipelines"])


def resolve_ai_model(provider: Optional[str], req_model: Optional[str]) -> str:
    if req_model and req_model.strip():
        return req_model.strip()
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")
    if provider == "groq":
        return os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    return os.getenv("OLLAMA_MODEL_NAME", "qwen3:8b")


def resolve_ai_key(provider: Optional[str], req_key: Optional[str]) -> Optional[str]:
    if req_key and req_key.strip():
        return req_key.strip()
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if provider == "groq":
        return os.getenv("GROQ_API_KEY")
    return None


@router.post("/link", response_model=LinkAuditResponse)
def audit_link(
    req: LinkAuditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches a single post/video from Instagram or YouTube and performs compliance + OCR audit."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post URL cannot be empty.")

    report = None
    platform = "Unknown"
    ai_model = resolve_ai_model(req.ai_provider, req.ai_model)
    ai_api_key = resolve_ai_key(req.ai_provider, req.ai_api_key)

    # --- 1. YouTube Single Video Ingestion ---
    if "youtube.com" in url or "youtu.be" in url:
        platform = "YouTube"
        video_id = extract_youtube_video_id(url)
        if not video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse YouTube video ID from URL."
            )

        api_key = req.yt_api_key or os.getenv("YOUTUBE_API_KEY") or os.getenv("YT_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube API Key is required. Please set YOUTUBE_API_KEY in .env or supply it in the request."
            )

        try:
            report = fetch_single_yt_video(
                video_id=video_id,
                api_key=api_key,
                enable_ai=req.enable_ai,
                provider=req.ai_provider,
                model_name=ai_model,
                ai_api_key=ai_api_key,
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"YouTube pipeline error: {str(e)}")

        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="YouTube video not found or private.")

    # --- 2. Instagram Single Post Ingestion ---
    elif "instagram.com" in url:
        platform = "Instagram"
        parsed_username, parsed_shortcode = extract_instagram_info(url)
        username = parsed_username or (req.ig_username.strip() if req.ig_username else None)

        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instagram creator username is required for Business Discovery API lookup."
            )
        if not parsed_shortcode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse shortcode from Instagram post URL."
            )

        token = req.ig_token or os.getenv("IG_ACCESS_TOKEN")
        account_id = req.ig_account_id or os.getenv("IG_ACCOUNT_ID")
        if not token or not account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instagram Access Token and Business Account ID are required."
            )

        try:
            report = fetch_single_ig_post(
                username=username,
                shortcode=parsed_shortcode,
                access_token=token,
                ig_account_id=account_id,
                enable_ai=req.enable_ai,
                provider=req.ai_provider,
                model_name=ai_model,
                api_key=ai_api_key,
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Instagram pipeline error: {str(e)}")

        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post '{parsed_shortcode}' not found under @{username}.")

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported URL format. Please provide a YouTube or Instagram post/reel link."
        )

    # --- 3. Persist in Database & Index in ChromaDB ---
    similar_past = find_similar_audits(
        caption=report.post_url,
        owner_id=current_user.id,
        top_k=3
    )

    db_record = AuditRecord(
        owner_id=current_user.id,
        platform=platform,
        content_type="video" if platform == "YouTube" else "static_post",
        material_connection="paid",
        caption=f"Imported from {report.post_url} by {report.influencer_handle}",
        influencer_handle=report.influencer_handle,
        post_url=report.post_url,
        status=report.caption_status,
        risk_level=report.risk_level,
        violations=json.dumps(report.caption_flags),
        expert_review=json.dumps(report.expert_review_flags),
        explanations=json.dumps({flag: f"Flagged rule: {flag}" for flag in report.caption_flags}),
        summary=f"Automated ingestion audit for {report.post_url}. Verdict: {report.caption_status} ({report.risk_level} RISK). Visual OCR status: {report.visual_status}.",
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    index_audit(
        audit_id=db_record.id,
        owner_id=current_user.id,
        caption=db_record.caption,
        status=db_record.status,
        risk_level=db_record.risk_level
    )

    return LinkAuditResponse(
        id=db_record.id,
        platform=platform,
        influencer_handle=report.influencer_handle,
        post_url=report.post_url,
        timestamp=report.timestamp,
        caption=db_record.caption,
        status=report.caption_status,
        risk_level=report.risk_level,
        caption_flags=report.caption_flags,
        visual_status=report.visual_status,
        visual_flags=report.visual_flags,
        is_compliant=report.is_compliant,
        ai_status=report.ai_status,
        ai_explanation=report.ai_explanation,
        ai_recommended_fix=report.ai_recommended_fix,
        ai_claims=report.ai_claims,
        similar_past_audits=[SimilarAudit(**item) for item in similar_past]
    )


@router.post("/account", response_model=AccountAuditResponse)
def audit_account(
    req: AccountAuditRequest,
    current_user: User = Depends(get_current_user),
):
    """Audits recent posts/videos of a creator profile or YouTube channel in batch."""
    url = req.account_url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account URL cannot be empty.")

    reports = []
    target_name = "Unknown"
    platform = "Unknown"
    ai_model = resolve_ai_model(req.ai_provider, req.ai_model)
    ai_api_key = resolve_ai_key(req.ai_provider, req.ai_api_key)

    if "youtube.com" in url:
        platform = "YouTube"
        handle, cid = extract_youtube_channel_info(url)
        if not handle and not cid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse YouTube handle or channel ID from URL (e.g., https://youtube.com/@channel)."
            )

        api_key = req.yt_api_key or os.getenv("YOUTUBE_API_KEY") or os.getenv("YT_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube API Key is required. Please set YOUTUBE_API_KEY in .env or pass it in the request."
            )

        try:
            target_name, reports = run_yt_pipeline(
                channel_handle_or_id=handle or cid,
                api_key=api_key,
                limit=req.limit,
                enable_ai=req.enable_ai,
                provider=req.ai_provider,
                model_name=ai_model,
                ai_api_key=ai_api_key,
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"YouTube channel audit failed: {str(e)}")

    elif "instagram.com" in url:
        platform = "Instagram"
        parts = [p for p in url.split("/") if p and "instagram.com" not in p]
        username = parts[0].replace("@", "") if parts else ""
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse Instagram username from URL."
            )

        target_name = f"@{username}"
        try:
            raw_reports = run_integrated_pipeline(
                target_username=username,
                enable_ai=req.enable_ai,
                provider=req.ai_provider,
                model_name=ai_model,
                api_key=ai_api_key,
            )
            reports = raw_reports[:req.limit]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Instagram account audit failed: {str(e)}")

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported profile URL. Please provide a YouTube channel or Instagram profile link."
        )

    total_audited = len(reports)
    compliant_count = sum(1 for r in reports if r.is_compliant)
    flagged_count = sum(1 for r in reports if r.caption_status == "FLAGGED")
    expert_review_count = sum(1 for r in reports if r.caption_status == "NEEDS EXPERT REVIEW")
    health_score = round((compliant_count / total_audited) * 100, 1) if total_audited > 0 else 0.0

    post_summaries = [
        AccountPostSummary(
            post_id=r.post_id,
            post_url=r.post_url,
            timestamp=r.timestamp,
            status=r.caption_status,
            risk_level=r.risk_level,
            is_compliant=r.is_compliant,
            caption_flags=r.caption_flags,
            visual_status=r.visual_status,
            visual_flags=r.visual_flags
        )
        for r in reports
    ]

    return AccountAuditResponse(
        platform=platform,
        target_name=target_name,
        total_audited=total_audited,
        compliant_count=compliant_count,
        flagged_count=flagged_count,
        expert_review_count=expert_review_count,
        health_score=health_score,
        posts=post_summaries
    )
