import logging
import os
from ultralytics import YOLO
from config import STAGE1_DIR, STAGE2_DIR, STAGE3_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelManager")


class ModelManager:
    def __init__(self):
        self.loaded_models = {}

    def _get_stage_dir(self, stage: str) -> str:
        if stage == "stage1":
            return STAGE1_DIR
        if stage == "stage2":
            return STAGE2_DIR
        if stage == "stage3":
            return STAGE3_DIR
        raise ValueError(f"Unknown stage: {stage}")

    def get_model(self, model_name: str = None, stage: str = "stage1"):
        stage_dir = self._get_stage_dir(stage)

        name = model_name
        if not name:
            available = self.list_available_models(stage)
            if not available:
                logger.warning(f"No models found for stage '{stage}'. Returning None.")
                return None
            name = available[0]

        cache_key = f"{stage}/{name}"
        if cache_key in self.loaded_models:
            return self.loaded_models[cache_key]

        model_path = os.path.join(stage_dir, name)
        if not os.path.exists(model_path):
            logger.warning(f"Model '{name}' not found at {model_path}. Returning None.")
            return None

        try:
            logger.info(f"Loading model: {name} for stage: {stage}...")
            self.loaded_models[cache_key] = YOLO(model_path)
            logger.info(f"Model '{name}' loaded successfully.")
            return self.loaded_models[cache_key]
        except Exception as e:
            logger.error(f"Failed to load model '{name}'. Error: {e}")
            return None

    def get_model_path(self, model_name: str, stage: str = "stage1") -> str | None:
        stage_dir = self._get_stage_dir(stage)
        path = os.path.join(stage_dir, model_name)
        return path if os.path.exists(path) else None

    def list_available_models(self, stage: str = "stage1"):
        stage_dir = self._get_stage_dir(stage)

        if not os.path.exists(stage_dir):
            return []

        return sorted(
            f
            for f in os.listdir(stage_dir)
            if not f.startswith(".")
            and f.endswith(".pt")
            and os.path.isfile(os.path.join(stage_dir, f))
        )

    def list_all_models(self):
        return {
            "stage1": self.list_available_models("stage1"),
            "stage2": self.list_available_models("stage2"),
            "stage3": self.list_available_models("stage3"),
        }


model_manager = ModelManager()
