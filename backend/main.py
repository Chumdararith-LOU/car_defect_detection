from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.host import router as host_router
from api.inspect import router as inspect_router
from api.models import router as models_router
from api.reviews import router as reviews_router
from api.system import router as system_router
from core.config import settings

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def init_review_db() -> None:
    # Importing services.review_db creates the data dir + schema on startup.
    from services.review_db import review_db  # noqa: F401


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(host_router)
app.include_router(system_router)
app.include_router(models_router)
app.include_router(inspect_router)
app.include_router(reviews_router)
