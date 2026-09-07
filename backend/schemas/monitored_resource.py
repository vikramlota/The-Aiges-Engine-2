from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MonitoredResourceCreate(BaseModel):
    platform: str = "Instagram"
    resource_id: str


class MonitoredResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    platform: str
    resource_id: str
    last_scraped_at: Optional[datetime] = None
    status: str
    created_at: datetime
