import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Campaign, AdChannel, AllocationRecommendation, utc_now
from backend.schemas import (
    CampaignCreate,
    CampaignResponse,
    AdChannelCreate,
    AdChannelResponse,
    ChannelShift,
    AllocationRecommendationResponse,
    ApproveRecommendationRequest,
)
from backend.auth import get_current_user
from backend.ad_allocation import run_thompson_sampling_optimizer

router = APIRouter(tags=["Ad Budget & Allocation"])


@router.post("/api/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    req: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates an advertising campaign for budget tracking and multi-armed bandit optimization."""
    campaign = Campaign(
        owner_id=current_user.id,
        name=req.name.strip(),
        total_monthly_budget=req.total_monthly_budget,
        currency=req.currency.strip().upper(),
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    if req.channels:
        for ch in req.channels:
            ad_ch = AdChannel(
                campaign_id=campaign.id,
                name=ch.name.strip(),
                current_allocation_pct=ch.current_allocation_pct,
                current_spend=ch.current_spend,
                impressions=ch.impressions,
                clicks=ch.clicks,
                conversions=ch.conversions,
                revenue=ch.revenue,
            )
            db.add(ad_ch)
        db.commit()
        db.refresh(campaign)

    return campaign


@router.get("/api/campaigns", response_model=List[CampaignResponse])
def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all advertising campaigns owned by the current user."""
    return db.query(Campaign).filter(Campaign.owner_id == current_user.id).order_by(Campaign.created_at.desc()).all()


@router.get("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves campaign details and current channel metrics."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.owner_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


@router.post("/api/campaigns/{campaign_id}/channels", response_model=AdChannelResponse, status_code=status.HTTP_201_CREATED)
def add_or_update_channel(
    campaign_id: int,
    req: AdChannelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adds a marketing channel or updates its latest performance metrics."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.owner_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    existing = db.query(AdChannel).filter(
        AdChannel.campaign_id == campaign.id,
        AdChannel.name == req.name.strip()
    ).first()

    if existing:
        existing.current_allocation_pct = req.current_allocation_pct
        existing.current_spend = req.current_spend
        existing.impressions = req.impressions
        existing.clicks = req.clicks
        existing.conversions = req.conversions
        existing.revenue = req.revenue
        existing.updated_at = utc_now()
        channel_to_return = existing
    else:
        new_ch = AdChannel(
            campaign_id=campaign.id,
            name=req.name.strip(),
            current_allocation_pct=req.current_allocation_pct,
            current_spend=req.current_spend,
            impressions=req.impressions,
            clicks=req.clicks,
            conversions=req.conversions,
            revenue=req.revenue,
        )
        db.add(new_ch)
        channel_to_return = new_ch

    db.commit()
    db.refresh(channel_to_return)
    return channel_to_return


@router.post("/api/campaigns/{campaign_id}/recommend", response_model=AllocationRecommendationResponse)
def generate_recommendation(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Runs Thompson Sampling multi-armed bandit algorithm across campaign channels.
    Generates an advisory budget shift recommendation with plain-language reasoning.
    Does NOT auto-apply any budget shifts (strict human approval requirement).
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.owner_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    channels = db.query(AdChannel).filter(AdChannel.campaign_id == campaign.id).all()
    if not channels or len(channels) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bandit optimization requires at least 2 ad channels configured in this campaign."
        )

    channel_data = [
        {
            "name": ch.name,
            "current_allocation_pct": ch.current_allocation_pct,
            "current_spend": ch.current_spend,
            "impressions": ch.impressions,
            "clicks": ch.clicks,
            "conversions": ch.conversions,
            "revenue": ch.revenue,
        }
        for ch in channels
    ]

    opt_result = run_thompson_sampling_optimizer(
        channels=channel_data,
        total_budget=campaign.total_monthly_budget
    )

    recommendation = AllocationRecommendation(
        campaign_id=campaign.id,
        recommended_shifts=json.dumps(opt_result["shifts"]),
        reasoning=opt_result["reasoning"],
        confidence=opt_result["confidence"],
        status="PENDING",
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return AllocationRecommendationResponse(
        id=recommendation.id,
        campaign_id=recommendation.campaign_id,
        shifts=[ChannelShift(**s) for s in opt_result["shifts"]],
        reasoning=recommendation.reasoning,
        confidence=recommendation.confidence,
        status=recommendation.status,
        approved_by=recommendation.approved_by,
        approved_at=recommendation.approved_at,
        created_at=recommendation.created_at,
    )


@router.post("/api/recommendations/{recommendation_id}/approve", response_model=AllocationRecommendationResponse)
def approve_recommendation(
    recommendation_id: int,
    req: ApproveRecommendationRequest = ApproveRecommendationRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Explicit human sign-off approving a budget reallocation recommendation.
    Updates the campaign channels' target allocation percentages.
    """
    rec = (
        db.query(AllocationRecommendation)
        .join(Campaign, Campaign.id == AllocationRecommendation.campaign_id)
        .filter(AllocationRecommendation.id == recommendation_id, Campaign.owner_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")

    if rec.status == "APPROVED":
        shifts_data = json.loads(rec.recommended_shifts) if rec.recommended_shifts else []
        return AllocationRecommendationResponse(
            id=rec.id,
            campaign_id=rec.campaign_id,
            shifts=[ChannelShift(**s) for s in shifts_data],
            reasoning=rec.reasoning,
            confidence=rec.confidence,
            status=rec.status,
            approved_by=rec.approved_by,
            approved_at=rec.approved_at,
            created_at=rec.created_at,
        )

    rec.status = "APPROVED"
    rec.approved_by = current_user.id
    rec.approved_at = utc_now()

    # Update channel allocation percentages
    shifts_data = json.loads(rec.recommended_shifts) if rec.recommended_shifts else []
    for s in shifts_data:
        ch = db.query(AdChannel).filter(
            AdChannel.campaign_id == rec.campaign_id,
            AdChannel.name == s["channel_name"]
        ).first()
        if ch:
            ch.current_allocation_pct = s["suggested_pct"]
            ch.updated_at = utc_now()

    db.commit()
    db.refresh(rec)

    return AllocationRecommendationResponse(
        id=rec.id,
        campaign_id=rec.campaign_id,
        shifts=[ChannelShift(**s) for s in shifts_data],
        reasoning=rec.reasoning,
        confidence=rec.confidence,
        status=rec.status,
        approved_by=rec.approved_by,
        approved_at=rec.approved_at,
        created_at=rec.created_at,
    )
