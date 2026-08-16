from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "cardefect-backend"
    api_v1_str: str = "/api"
    workspace_root: Path = Path(__file__).resolve().parents[2]
    allow_cpu_inference: bool = True

    tau_pixel: float = 0.70
    tau_anomaly: float = 0.0005

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
