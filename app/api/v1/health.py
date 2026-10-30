"""Health check endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", summary="System Health Check")
async def health_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    """Verify application status, version, and database connectivity."""
    db_status = "connected"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
    }
