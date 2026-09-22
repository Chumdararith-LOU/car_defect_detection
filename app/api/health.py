"""Health, liveness, and version endpoints."""
import time

from fastapi import APIRouter

from app.config import settings
from app.core.device import resolve_device

router = APIRouter(prefix=settings.api_v1_str, tags=["health"])

_START_TIME = time.time()


@router.get("/health")
def health():
    """Liveness + readiness probe."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "device": resolve_device(settings.device),
        "uptime_seconds": round(time.time() - _START_TIME, 1),
    }


@router.get("/version")
def version():
    """Service version."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
    }
