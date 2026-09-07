### Recommended Folder Structure

```text
backend/
├── database.py              # Declares engine, SessionLocal, and Base = declarative_base()
├── models/                  # Models package
│   ├── __init__.py          # Re-exports all models & registers them with SQLAlchemy
│   ├── base.py              # (Optional) shared utilities like timestamp helpers
│   ├── user.py              # User model
│   ├── audit.py             # Audit model
│   ├── mention.py           # Mention model
│   └── campaign.py          # Campaign, AdChannel, AllocationRecommendation models
├── schemas/                 # Pydantic Schemas package
│   ├── __init__.py          # Re-exports schemas for convenient imports
│   ├── common.py            # Shared schemas (e.g. pagination, error models)
│   ├── user.py              # UserCreate, UserLogin, UserResponse, Token
│   ├── audit.py             # AuditRequest, AuditResponse, AccountAuditRequest
│   ├── mention.py           # MentionIngestRequest, MentionResponse, AnomalyReport
│   └── campaign.py          # CampaignCreate, RecommendationResponse
└── routers/                 # API Endpoints (already modularized)
    ├── auth.py
    ├── audits.py
    ├── mentions.py
    └── ad_allocation.py
```

---

### 3 Rules to Follow When Modularizing

#### 1. Avoid Circular Imports with SQLAlchemy Relationships
When models reference each other via foreign keys or relationships (e.g., `User` has many `Mention`s, and `Mention` belongs to `User`):
- **Define `Base` once** in `database.py` and import `Base` into each model file.
- In `relationship()`, **always use string names** rather than importing the class directly:
  ```python
  # In backend/models/mention.py
  from sqlalchemy import Column, Integer, ForeignKey, String
  from sqlalchemy.orm import relationship
  from backend.database import Base

  class Mention(Base):
      __tablename__ = "mentions"
      id = Column(Integer, primary_key=True)
      owner_id = Column(Integer, ForeignKey("users.id"))

      # Use string "User" instead of importing User directly:
      owner = relationship("User", back_populates="mentions")
  ```

#### 2. Re-Export in `models/__init__.py` for Metadata Registration
SQLAlchemy needs all model classes imported into Python's memory so that `Base.metadata.create_all(bind=engine)` and Alembic migrations discover all tables. In `backend/models/__init__.py`:

```python
# backend/models/__init__.py
from backend.models.user import User
from backend.models.audit import Audit
from backend.models.mention import Mention
from backend.models.campaign import Campaign, AdChannel, AllocationRecommendation

__all__ = [
    "User",
    "Audit",
    "Mention",
    "Campaign",
    "AdChannel",
    "AllocationRecommendation",
]
```
**Bonus:** This allows existing imports across your code (such as `from backend.models import Mention, User`) to keep working without rewriting individual import paths.

#### 3. Group Pydantic Schemas by Feature Area
In `backend/schemas/`:
- Keep request/response schemas closely tied to their domain.
- In `backend/schemas/__init__.py`, re-export the commonly used schemas so router files can do:
  ```python
  from backend.schemas.mention import MentionResponse, MentionSummaryResponse
  # OR
  from backend.schemas import MentionResponse, MentionSummaryResponse
  ```

### Summary of Benefits
1. **Maintainability:** Each file focuses on a single domain entity (typically 50–150 lines instead of a single 500+ line monolith).
2. **Team Collaboration:** Prevents git merge conflicts when different developers work on audits, campaigns, and sentiment simultaneously.
3. **Reusability:** Easier to locate, test, and refactor individual business models.