"""Car-defect inference API — application entrypoint.

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import batch, crops, health, inspect, meta
from app.config import settings
from app.core.device import resolve_device
from app.core.model_registry import model_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload required models and prepare storage on startup."""
    settings.ensure_dirs()
    device = resolve_device(settings.device)
    logger.info("Preloading required models on device=%s ...", device)
    for info in model_registry.list_models():
        if info["required"]:
            try:
                model_registry.get_model(info["name"], device=device)
                logger.info("Preloaded model '%s'", info["name"])
            except Exception as e:  # noqa: BLE001
                logger.warning("Could not preload model '%s': %s", info["name"], e)
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(meta.router)
app.include_router(inspect.router)
app.include_router(crops.router)
app.include_router(batch.router)
