"""Application settings for the inference API.

All settings can be overridden via environment variables prefixed with
``INFERENCE_API_`` or a local ``.env`` file.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# inference-api/ repository root (this file lives in app/)
APP_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime configuration for the inference service."""

    app_name: str = "car-defect-inference-api"
    app_version: str = "1.0.0"
    api_v1_str: str = "/v1"

    # Filesystem layout (resolved relative to the repo root)
    models_dir: Path = APP_ROOT / "models"
    configs_dir: Path = APP_ROOT / "configs"
    storage_dir: Path = APP_ROOT / "storage"
    crops_dir: Path = APP_ROOT / "storage" / "crops"
    jobs_dir: Path = APP_ROOT / "storage" / "jobs"

    # Inference defaults
    device: str = "auto"              # auto | cuda | mps | cpu
    default_preset: str = "safety"
    production_config: str = "production.yaml"

    # Job queue
    max_workers: int = 1              # keep 1 for GPU safety

    # CORS (internal service, no auth)
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:8080",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:8080",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="INFERENCE_API_",
        extra="ignore",
    )

    def ensure_dirs(self) -> None:
        """Create runtime storage directories if they do not exist."""
        for d in (self.storage_dir, self.crops_dir, self.jobs_dir):
            Path(d).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
