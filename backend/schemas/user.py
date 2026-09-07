from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# --- Auth Schemas ---

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
