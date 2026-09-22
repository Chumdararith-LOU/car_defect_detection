"""Metadata endpoints: operating presets, taxonomy, and registered models."""
import yaml
from fastapi import APIRouter

from app.config import settings
from app.core.model_registry import model_registry
from app.pipeline.stage3_panel import PANEL_CLASS_NAMES

router = APIRouter(prefix=settings.api_v1_str, tags=["meta"])

# Canonical 7-class defect taxonomy (broken_part is canonical; broken_lamp is
# normalized to broken_part internally and never appears in output).
DEFECT_CLASSES = [
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_part",
    "corrosion",
    "disjoint_part",
]


@router.get("/presets")
def list_presets():
    """List available operating presets and their routing strategies."""
    config_path = settings.configs_dir / settings.production_config
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return {
        "presets": cfg.get("presets", {}),
        "routing_strategy": cfg.get("routing_strategy", {}),
    }


@router.get("/taxonomy")
def taxonomy():
    """Return the 7 defect classes and the 21 panel classes."""
    return {
        "defect_classes": DEFECT_CLASSES,
        "panel_classes": PANEL_CLASS_NAMES,
    }


@router.get("/models")
def list_models():
    """List all models in the registry with load status."""
    return {"models": model_registry.list_models()}
