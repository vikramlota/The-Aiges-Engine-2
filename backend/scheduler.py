import os
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database import SessionLocal
from backend.models import MonitoredResource, Mention, utc_now
from backend.sentiment import analyze_comment

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def fetch_mock_comments_for_resource(resource: MonitoredResource) -> list:
    """Mock comment generator since we don't have real Instagram webhooks configured yet."""
    return [
        {
            "text": "This product is amazing! Loved the demo.",
            "author_handle": "@happy_user",
            "detected_at": utc_now()
        },
        {
            "text": "Worst experience ever. The delivery was 3 days late and support ignored me.",
            "author_handle": "@angry_customer",
            "detected_at": utc_now()
        }
    ]

def process_monitored_resources(db=None):
    """
    Background job to poll social APIs for tracked resources.
    Executes in a separate thread/event loop from web requests.
    """
    logger.info("Starting automated data ingestion polling cycle...")
    
    # We must create a new DB session for the background task if not provided (for tests)
    session = db or SessionLocal()
    try:
        # Get active resources that haven't been scraped in the last 1 minute 
        # (Using 1 minute for MVP/Demo purposes; in prod this would be 15-60 mins)
        cutoff = utc_now() - timedelta(minutes=1)
        
        resources_to_poll = session.query(MonitoredResource).filter(
            MonitoredResource.status == "active",
            (MonitoredResource.last_scraped_at == None) | (MonitoredResource.last_scraped_at < cutoff)
        ).all()
        
        if not resources_to_poll:
            logger.info("No resources due for polling.")
            return

        for resource in resources_to_poll:
            logger.info(f"Polling {resource.platform} resource {resource.resource_id}...")
            
            # Fetch comments (using mock for now, but easily swappable with IG Graph API)
            new_comments = fetch_mock_comments_for_resource(resource)
            
            for item in new_comments:
                # Avoid duplicate comments by checking text and author for this post
                # In real life we'd use comment_id from the API
                exists = session.query(Mention).filter(
                    Mention.post_id == resource.resource_id,
                    Mention.author_handle == item["author_handle"],
                    Mention.text == item["text"]
                ).first()
                
                if not exists:
                    analysis = analyze_comment(item["text"])
                    mention = Mention(
                        owner_id=resource.owner_id,
                        post_id=resource.resource_id,
                        platform=resource.platform,
                        author_handle=item["author_handle"],
                        text=item["text"],
                        sentiment=analysis["sentiment"],
                        sentiment_score=analysis["sentiment_score"],
                        detected_at=item["detected_at"],
                        flagged_for_review=analysis["flagged_for_review"],
                        explanation=analysis["explanation"],
                        language=analysis.get("language", "en")
                    )
                    session.add(mention)
            
            # Update scrape timestamp
            resource.last_scraped_at = utc_now()
            session.commit()
            
    except Exception as e:
        logger.error(f"Error during polling cycle: {e}")
        session.rollback()
    finally:
        if not db:
            session.close()

def start_scheduler():
    """Initializes and starts the APScheduler background worker."""
    # Run every 60 seconds for demo purposes
    scheduler.add_job(
        process_monitored_resources,
        trigger=IntervalTrigger(seconds=60),
        id="ingestion_polling_job",
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    logger.info("Automated Ingestion Scheduler started.")

def stop_scheduler():
    """Gracefully shuts down the scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Automated Ingestion Scheduler stopped.")
