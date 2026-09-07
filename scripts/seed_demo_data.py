"""
Demo Data Seeding Script for The Aiges Engine.

Seeds:
1. Demo User: demo@aiges.ai / password123
2. Sample ASCI Compliance Audit Records
3. Sample Multilingual Sentiment Mentions (English, Hinglish, Indic scripts)
4. Sample Marketing Campaign with Multi-Armed Bandit Channels & Recommendations

Run:
    python3 scripts/seed_demo_data.py
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import SessionLocal, engine, Base
import backend.models
from backend.models import User, AuditRecord, Mention, Campaign, AdChannel, AllocationRecommendation
from backend.utils.security import hash_password
from backend.sentiment import analyze_comment
from backend.ad_allocation import run_thompson_sampling_optimizer


def seed_data():
    print("=" * 60)
    print("The Aiges Engine — Seeding Demo Environment")
    print("=" * 60)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create or fetch Demo User
        demo_email = "demo@aiges.ai"
        user = db.query(User).filter(User.email == demo_email).first()
        if not user:
            user = User(
                email=demo_email,
                hashed_password=hash_password("password123"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created demo user: {demo_email} (password: password123)")
        else:
            print(f"ℹ️ Demo user already exists: {demo_email}")

        # 2. Seed Sample Compliance Audits
        existing_audits = db.query(AuditRecord).filter(AuditRecord.owner_id == user.id).count()
        if existing_audits == 0:
            sample_audits = [
                AuditRecord(
                    owner_id=user.id,
                    platform="Instagram",
                    content_type="reel_story",
                    material_connection="paid",
                    caption="#ad Loving this new skincare serum! Genuine results in 2 weeks. #collab",
                    influencer_handle="@priya_skincare",
                    post_url="https://instagram.com/p/sample_audit_1",
                    status="COMPLIANT",
                    risk_level="LOW",
                    violations="[]",
                    expert_review="[]",
                    explanations="{}",
                    summary="Fully compliant. Prominent '#ad' disclosure present at the beginning of caption.",
                ),
                AuditRecord(
                    owner_id=user.id,
                    platform="Instagram",
                    content_type="static_post",
                    material_connection="gifted_barter",
                    caption="Had so much fun trying out this watch! #style #trending #fashion",
                    influencer_handle="@fashion_sam",
                    post_url="https://instagram.com/p/sample_audit_2",
                    status="FLAGGED",
                    risk_level="HIGH",
                    violations='["Missing mandatory commercial disclosure hashtag (#ad, #collab, or #partnership)"]',
                    expert_review="[]",
                    explanations='{"missing_disclosure": "ASCI Guidelines require prominent disclosure for gifted/barter collaborations."}',
                    summary="Flagged for review: Commercial connection exists but no disclosure tag was found.",
                )
            ]
            db.add_all(sample_audits)
            db.commit()
            print(f"✅ Seeded {len(sample_audits)} sample compliance audits")
        else:
            print(f"ℹ️ {existing_audits} audits already present for demo user")

        # 3. Seed Sample Multilingual Mentions
        existing_mentions = db.query(Mention).filter(Mention.owner_id == user.id).count()
        if existing_mentions == 0:
            raw_comments = [
                ("@rahul_m", "Loved the packaging, fast shipping and great product!"),
                ("@ananya_g", "The package arrived damaged and customer care refused refund, total scam!"),
                ("@harsh_delhi", "Bhai bilkul bekaar customer service hai, delivery late aayi aur paisa barbaad!"),
                ("@pooja_p", "यह उत्पाद सच में बहुत अच्छा और असरदार है, मुझे बहुत पसंद आया!"),
                ("@arjun_99", "Ekdum ghatiya experience, counterfeit product. Seller cheated me!"),
                ("@simran_k", "Packaging bohot zabardast hai, premium look!"),
            ]

            now = datetime.now(timezone.utc)
            seeded_mentions = []
            for i, (handle, text) in enumerate(raw_comments):
                analysis = analyze_comment(text)
                detected_at = now - timedelta(hours=i * 4)
                m = Mention(
                    owner_id=user.id,
                    post_id="ig_demo_post_1",
                    platform="Instagram",
                    author_handle=handle,
                    text=text,
                    sentiment=analysis["sentiment"],
                    sentiment_score=analysis["sentiment_score"],
                    flagged_for_review=analysis["flagged_for_review"],
                    explanation=analysis["explanation"],
                    language=analysis.get("language", "en"),
                    detected_at=detected_at,
                )
                seeded_mentions.append(m)

            db.add_all(seeded_mentions)
            db.commit()
            print(f"✅ Seeded {len(seeded_mentions)} multilingual sentiment mentions (EN, Hinglish, Indic)")
        else:
            print(f"ℹ️ {existing_mentions} mentions already present for demo user")

        # 4. Seed Sample Ad Campaign & Optimization Channels
        existing_campaigns = db.query(Campaign).filter(Campaign.owner_id == user.id).count()
        if existing_campaigns == 0:
            campaign = Campaign(
                owner_id=user.id,
                name="Q4 D2C Festive Scaling Pilot",
                total_monthly_budget=150000.0,
                currency="INR",
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)

            channels = [
                AdChannel(campaign_id=campaign.id, name="Instagram Reels", current_allocation_pct=35.0, current_spend=52500.0, impressions=120000, clicks=4800, conversions=240, revenue=187200.0),
                AdChannel(campaign_id=campaign.id, name="YouTube Shorts", current_allocation_pct=25.0, current_spend=37500.0, impressions=95000, clicks=3100, conversions=155, revenue=120900.0),
                AdChannel(campaign_id=campaign.id, name="Meta Feed", current_allocation_pct=25.0, current_spend=37500.0, impressions=80000, clicks=2000, conversions=85, revenue=59500.0),
                AdChannel(campaign_id=campaign.id, name="Google Search Ads", current_allocation_pct=15.0, current_spend=22500.0, impressions=30000, clicks=1800, conversions=110, revenue=99000.0),
            ]
            db.add_all(channels)
            db.commit()

            # Run initial Thompson Sampling Recommendation
            channel_dicts = [
                {
                    "name": c.name,
                    "current_allocation_pct": c.current_allocation_pct,
                    "current_spend": c.current_spend,
                    "conversions": c.conversions,
                    "revenue": c.revenue,
                }
                for c in channels
            ]
            rec = run_thompson_sampling_optimizer(channel_dicts, total_budget=campaign.total_monthly_budget)
            
            import json
            recommendation = AllocationRecommendation(
                campaign_id=campaign.id,
                recommended_shifts=json.dumps(rec["shifts"]),
                reasoning=rec["reasoning"],
                confidence=rec["confidence"],
                status="PENDING",
            )
            db.add(recommendation)
            db.commit()
            print(f"✅ Seeded Campaign '{campaign.name}' with 4 channels & Thompson Sampling recommendation")
        else:
            print(f"ℹ️ {existing_campaigns} campaigns already present for demo user")

        print("=" * 60)
        print("🎉 Demo data seeding complete! You can log in as:")
        print(f"   Email:    demo@aiges.ai")
        print(f"   Password: password123")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
