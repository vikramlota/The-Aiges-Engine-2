import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure the project root directory is in sys.path so that imports of
# 'backend', 'core', and 'pipelines' work regardless of where the command is invoked.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.database import engine, Base
import backend.models  # Ensures all models are registered on Base.metadata
from backend.routers import health, meta, auth, audits, pipelines, mentions, ad_allocation
from backend.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on application startup
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="The Aiges Engine Compliance API",
    description="ASCI / CCPA Advertising Compliance Audit API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React / Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(meta.router)
app.include_router(auth.router)
app.include_router(audits.router)
app.include_router(pipelines.router)
app.include_router(mentions.router)
app.include_router(ad_allocation.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

