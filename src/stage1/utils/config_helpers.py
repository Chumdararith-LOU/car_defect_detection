import yaml
import torch
import logging


def load_pipeline_config(config_path: str = "configs/pipeline_config.yaml") -> dict:
    """Loads and returns the pipeline configuration dictionary."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def resolve_device(config: dict) -> torch.device:
    """
    Resolves the execution target device following the priority order:
    1. CUDA if available (RTX 3090 Server)
    2. MPS if available (MacBook Apple Silicon)
    3. CPU fallback
    """
    logger = logging.getLogger("PipelineConfig")

    if torch.cuda.is_available():
        device_idx = config.get("hardware", {}).get("device", 0)
        device_str = f"cuda:{device_idx}"
        logger.info(f"Targeting CUDA Device: {torch.cuda.get_device_name(device_idx)}")
        return torch.device(device_str)
    elif torch.backends.mps.is_available():
        logger.info("Targeting Apple Silicon Metal Performance Shaders (MPS).")
        return torch.device("mps")
    else:
        logger.info("Targeting CPU Execution.")
        return torch.device("cpu")
