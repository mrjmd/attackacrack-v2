from fastapi import APIRouter, Depends, Response
from datetime import datetime
from app.core.config import Settings, get_settings

router = APIRouter()

@router.get("", tags=["health"])
async def health_check(response: Response, settings: Settings = Depends(get_settings)):
    """
    Health check endpoint that returns system status.
    
    Returns basic health information including status, timestamp, and version.
    Designed to be lightweight and respond quickly (<100ms).
    """
    # Set cache-control headers to prevent caching
    response.headers["cache-control"] = "no-cache"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.app_version
    }