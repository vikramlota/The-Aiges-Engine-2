from fastapi import APIRouter
from core.rules import PLATFORMS, CONTENT_TYPES, MATERIAL_CONNECTIONS, ASCI_CATEGORIES
from backend.schemas import MetaResponse, MaterialConnectionItem, ExpertReviewCategoryItem

router = APIRouter(tags=["Meta"])


@router.get("/api/meta", response_model=MetaResponse)
def get_metadata():
    """Returns rule engine metadata so frontend never hardcodes a second copy."""
    connections = [
        MaterialConnectionItem(key=k, label=v)
        for k, v in MATERIAL_CONNECTIONS.items()
    ]
    expert_categories = [
        ExpertReviewCategoryItem(
            key=k,
            label=v["label"],
            source=v.get("source", "")
        )
        for k, v in ASCI_CATEGORIES.items()
        if v.get("automated") is not True  # non-automated and partial need reviewer input
    ]
    return MetaResponse(
        platforms=PLATFORMS,
        content_types=CONTENT_TYPES,
        material_connections=connections,
        expert_review_categories=expert_categories,
    )
