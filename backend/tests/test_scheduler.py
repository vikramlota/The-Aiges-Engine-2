import pytest
from backend.models import MonitoredResource, Mention, User
from backend.scheduler import process_monitored_resources

def test_scheduler_polling_logic(db_session):
    # Create test user
    user = User(email="scheduler@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    # Create a monitored resource
    resource = MonitoredResource(
        owner_id=user.id,
        platform="Instagram",
        resource_id="post_123"
    )
    db_session.add(resource)
    db_session.commit()
    
    # Run the polling cycle
    process_monitored_resources(db=db_session)
    
    # Verify the resource was updated
    db_session.refresh(resource)
    assert resource.last_scraped_at is not None
    
    # Verify mock mentions were injected
    mentions = db_session.query(Mention).filter(Mention.post_id == "post_123").all()
    assert len(mentions) == 2
    
    # Test deduplication: running it again shouldn't add the same comments
    process_monitored_resources(db=db_session)
    mentions_after = db_session.query(Mention).filter(Mention.post_id == "post_123").all()
    assert len(mentions_after) == 2  # Still 2
