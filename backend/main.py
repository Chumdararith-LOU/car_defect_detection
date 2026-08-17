from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.host import router as host_router
from api.inspect import router as inspect_router
from api.dataset_images import router as dataset_images_router
from api.datasets import router as datasets_router
from api.models import router as models_router
from api.reviews import router as reviews_router
from api.dataset_import import router as dataset_import_router
from api.system import router as system_router
from api.training import router as training_router
from core.config import settings
from api.dataset_prep import router as dataset_prep_router
from api.experiments import router as experiments_router
from api.model_registry import router as model_registry_router
from api.taxonomy import router as taxonomy_router
from api.checkpoints import router as checkpoints_router

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def init_review_db() -> None:
    from services.review_db import review_db  # noqa: F401


@app.on_event("startup")
def init_platform_tables() -> None:
    from services.checkpoint_registry import ensure_native_checkpoints
    from services.platform_db import init_platform_tables as _init
    from services.taxonomy_service import ensure_default_taxonomies

    _init()
    ensure_default_taxonomies()
    ensure_native_checkpoints()


origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(host_router, prefix="/api")
app.include_router(system_router)
app.include_router(models_router)
app.include_router(inspect_router)
app.include_router(reviews_router)
app.include_router(datasets_router)
app.include_router(dataset_images_router)
app.include_router(dataset_import_router)
app.include_router(training_router)
app.include_router(dataset_prep_router)
app.include_router(experiments_router)
app.include_router(model_registry_router)
app.include_router(taxonomy_router)
app.include_router(checkpoints_router)
