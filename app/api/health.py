import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db

router = APIRouter()
START_TIME = time.time()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Health check endpoint for container orchestrators (Railway / Render / Docker)."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    uptime_seconds = int(time.time() - START_TIME)

    return {
        "data": {
            "status": "ok",
            "version": "0.1.0",
            "environment": settings.app_env,
            "cromaMode": settings.croma_mode,
            "uptimeSeconds": uptime_seconds,
            "database": db_status,
        }
    }
