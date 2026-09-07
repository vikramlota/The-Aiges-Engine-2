from typing import List, Optional
from pydantic import BaseModel


# --- Meta Schemas ---

class MaterialConnectionItem(BaseModel):
    key: str
    label: str


class ExpertReviewCategoryItem(BaseModel):
    key: str
    label: str
    source: Optional[str] = ""


class MetaResponse(BaseModel):
    platforms: List[str]
    content_types: List[str]
    material_connections: List[MaterialConnectionItem]
    expert_review_categories: List[ExpertReviewCategoryItem]
