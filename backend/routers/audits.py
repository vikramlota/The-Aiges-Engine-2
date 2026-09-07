import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, AuditRecord
from backend.schemas import AuditCreate, AuditResponse, AuditListItem, SimilarAudit
from backend.auth import get_current_user
from backend.vector_store import index_audit, find_similar_audits

from core.engine import PostInput, audit_post
from core.rules import CONTENT_TYPES, MATERIAL_CONNECTIONS, ASCI_CATEGORIES

router = APIRouter(prefix="/api/audits", tags=["Audits"])


@router.post("", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
def create_audit(
    audit_data: AuditCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Validation against rule engine dictionaries
    if audit_data.content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid content_type '{audit_data.content_type}'. Must be one of {CONTENT_TYPES}."
        )

    if audit_data.material_connection not in MATERIAL_CONNECTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid material_connection '{audit_data.material_connection}'. Must be one of {list(MATERIAL_CONNECTIONS.keys())}."
        )

    for cat in audit_data.content_categories:
        if cat not in ASCI_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid content_category '{cat}'. Must be one of {list(ASCI_CATEGORIES.keys())}."
            )

    # 2. Construct PostInput and execute compliance audit
    post = PostInput(
        platform=audit_data.platform,
        content_type=audit_data.content_type,
        material_connection=audit_data.material_connection,
        caption=audit_data.caption or "",
        influencer_handle=audit_data.influencer_handle or "",
        post_url=audit_data.post_url or "",
        is_virtual_influencer=audit_data.is_virtual_influencer,
        ai_disclosure_present_and_persistent=audit_data.ai_disclosure_present_and_persistent,
        makes_health_finance_or_technical_claim=audit_data.makes_health_finance_or_technical_claim,
        credentials_or_substantiation_shown=audit_data.credentials_or_substantiation_shown,
        video_verbal_disclosure_second=audit_data.video_verbal_disclosure_second,
        video_overlay_covers_sponsored_segment=audit_data.video_overlay_covers_sponsored_segment,
        story_label_superimposed=audit_data.story_label_superimposed,
        ai_generated_or_enhanced=audit_data.ai_generated_or_enhanced,
        ai_content_label_present=audit_data.ai_content_label_present,
        names_specific_competitor=audit_data.names_specific_competitor,
        unqualified_superiority_claim=audit_data.unqualified_superiority_claim,
        product_category=audit_data.product_category,
        mandatory_disclaimer_present=audit_data.mandatory_disclaimer_present,
        content_categories=audit_data.content_categories,
    )

    result = audit_post(post)

    # 3. Find similar past audits BEFORE adding current one (or excluding current)
    similar_past = find_similar_audits(
        caption=post.caption,
        owner_id=current_user.id,
        top_k=3
    )

    # 4. Save to Database
    db_record = AuditRecord(
        owner_id=current_user.id,
        platform=post.platform,
        content_type=post.content_type,
        material_connection=post.material_connection,
        caption=post.caption,
        influencer_handle=post.influencer_handle,
        post_url=post.post_url,
        status=result.status,
        risk_level=result.risk_level,
        violations=json.dumps(result.violations),
        expert_review=json.dumps(result.expert_review),
        explanations=json.dumps(result.explanations),
        summary=result.summary(),
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # 5. Index in ChromaDB for future queries
    index_audit(
        audit_id=db_record.id,
        owner_id=current_user.id,
        caption=post.caption,
        status=result.status,
        risk_level=result.risk_level
    )

    return AuditResponse(
        id=db_record.id,
        status=db_record.status,
        risk_level=db_record.risk_level,
        violations=result.violations,
        expert_review=result.expert_review,
        explanations=result.explanations,
        summary=db_record.summary,
        caption=db_record.caption,
        created_at=db_record.created_at,
        similar_past_audits=[SimilarAudit(**item) for item in similar_past],
    )


@router.get("", response_model=List[AuditListItem])
def list_user_audits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve audit history for the authenticated user only."""
    records = (
        db.query(AuditRecord)
        .filter(AuditRecord.owner_id == current_user.id)
        .order_by(AuditRecord.created_at.desc())
        .all()
    )
    return records


@router.get("/{audit_id}", response_model=AuditResponse)
def get_audit_detail(
    audit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve single audit detail if owned by the authenticated user (404 otherwise)."""
    record = (
        db.query(AuditRecord)
        .filter(AuditRecord.id == audit_id, AuditRecord.owner_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit record not found."
        )

    # Parse stored JSON fields
    try:
        violations = json.loads(record.violations)
    except Exception:
        violations = []

    try:
        expert_review = json.loads(record.expert_review)
    except Exception:
        expert_review = []

    try:
        explanations = json.loads(record.explanations)
    except Exception:
        explanations = {}

    # Freshly computed similar past audits
    similar_past = find_similar_audits(
        caption=record.caption,
        owner_id=current_user.id,
        exclude_id=record.id,
        top_k=3
    )

    return AuditResponse(
        id=record.id,
        status=record.status,
        risk_level=record.risk_level,
        violations=violations,
        expert_review=expert_review,
        explanations=explanations,
        summary=record.summary,
        caption=record.caption,
        created_at=record.created_at,
        similar_past_audits=[SimilarAudit(**item) for item in similar_past],
    )
