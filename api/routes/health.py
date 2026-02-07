"""Health check endpoints."""

from fastapi import APIRouter

from config.settings import get_settings
from database.connection import check_db_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check including dependencies."""
    settings = get_settings()
    
    # Check database connection
    db_healthy = await check_db_connection()
    
    status = "ready" if db_healthy else "not_ready"
    
    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
        },
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check - just confirms the service is running."""
    return {"status": "alive"}
