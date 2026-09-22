"""Model registry: discovers, loads, caches, and serves production model weights.

The registry reads ``models/manifest.json`` to learn which checkpoints belong to
which pipeline stage, loads them on demand, and caches them in memory so repeated
requests do not re-read from disk.

Stage 2 checkpoints are loaded as ``sahi.AutoDetectionModel`` (the form required
by Slicing Aided Hyper Inference). Stage 1 and Stage 3 checkpoints are loaded as
``ultralytics.YOLO`` (the form required by their direct-call inference).

Importing this module also registers the custom ``Segment26WithObjectness`` head
(via ``app.core.head_registry``) so objectness checkpoints can be unpickled.
"""
import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List

from app.config import settings
from app.core.head_registry import register_custom_head

logger = logging.getLogger("model_registry")

# Register the custom objectness head as soon as the registry is imported so any
# subsequent checkpoint load can unpickle Segment26WithObjectness.
register_custom_head()

# Floor confidence for Stage 2 models. Set to the lowest per-class confidence used
# by any shipped preset (max_recall: corrosion / disjoint_part = 0.05) so a single
# cached model instance can serve every preset; the Stage 2 pipeline's per-class
# acceptance rules do the actual filtering.
_STAGE2_CONF_FLOOR = 0.05


class ModelNotFoundError(RuntimeError):
    """Raised when a requested model is missing from the manifest or from disk."""


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ModelRegistry:
    """Loads and caches model checkpoints described by ``models/manifest.json``."""

    def __init__(self) -> None:
        self._cache: Dict[str, object] = {}
        self._lock = threading.Lock()
        self._manifest = self._load_manifest()

    # ------------------------------------------------------------- manifest

    def _load_manifest(self) -> dict:
        manifest_path = settings.models_dir / "manifest.json"
        if not manifest_path.exists():
            raise ModelNotFoundError(f"manifest not found: {manifest_path}")
        return json.loads(manifest_path.read_text())

    def _find_entry(self, name: str) -> dict:
        for m in self._manifest["models"]:
            if m["name"] == name:
                return m
        raise ModelNotFoundError(f"model '{name}' not found in manifest")

    # ------------------------------------------------------------- queries

    def list_models(self) -> List[dict]:
        """Return metadata for every model in the manifest."""
        out = []
        for m in self._manifest["models"]:
            path = settings.models_dir / m["stage"] / m["filename"]
            out.append(
                {
                    "name": m["name"],
                    "stage": m["stage"],
                    "role": m["role"],
                    "required": m["required"],
                    "on_disk": path.exists(),
                    "loaded": any(
                        k.startswith(m["name"] + "@") for k in self._cache
                    ),
                }
            )
        return out

    def get_model_path(self, name: str) -> Path:
        entry = self._find_entry(name)
        path = settings.models_dir / entry["stage"] / entry["filename"]
        if not path.exists():
            raise ModelNotFoundError(f"weights not on disk: {path}")
        return path

    def verify_checksum(self, name: str) -> bool:
        """Return True if the on-disk weights match the manifest sha256."""
        entry = self._find_entry(name)
        expected = entry.get("sha256")
        if not expected:
            return True  # no checksum recorded; nothing to verify
        return _sha256_of(self.get_model_path(name)) == expected

    # ------------------------------------------------------------- loading

    def get_model(self, name: str, device: str = "cpu"):
        """Load (or return the cached) model ``name`` on ``device``."""
        cache_key = f"{name}@{device}"
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        entry = self._find_entry(name)
        path = self.get_model_path(name)
        stage = entry["stage"]

        logger.info("Loading model '%s' (stage=%s) on %s ...", name, stage, device)
        if stage == "stage2":
            model = self._load_stage2(path, device)
        else:
            model = self._load_yolo(path)
        logger.info("Model '%s' loaded (%s).", name, type(model).__name__)

        with self._lock:
            self._cache[cache_key] = model
        return model

    def preload_required(self, device: str = "cpu") -> List[str]:
        """Load every model marked ``required`` in the manifest. Returns names."""
        loaded = []
        for m in self._manifest["models"]:
            if m["required"]:
                self.get_model(m["name"], device=device)
                loaded.append(m["name"])
        return loaded

    # ------------------------------------------------------------- backends

    def _load_yolo(self, path: Path):
        from ultralytics import YOLO

        return YOLO(str(path))

    def _load_stage2(self, path: Path, device: str):
        from sahi import AutoDetectionModel

        return AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=str(path),
            confidence_threshold=_STAGE2_CONF_FLOOR,
            device=device,
        )


model_registry = ModelRegistry()
