import logging
import time
import numpy as np

from core.config import settings

logger = logging.getLogger("Stage1")


def run_prescreen(img_np: np.ndarray, model, device: str = "cpu") -> dict:
    """
    Runs the Stage 1 SOD model and calculates saliency metrics.
    Returns a dictionary with the results needed for the orchestrator.
    """
    start_time = time.time()
    results = model(img_np, device=device, verbose=False)
    result = results[0]
    latency_ms = (time.time() - start_time) * 1000.0

    # Fallback if model doesn't output semantic mask
    if not hasattr(result, "semantic_mask") or result.semantic_mask is None:
        return {
            "is_active": False,
            "saliency_score": 0.0,
            "binary_mask": None,
            "latency_ms": latency_ms,
            "error": "No semantic_mask output",
        }

    saliency_map = result.semantic_mask.data.cpu().numpy()
    h, w = saliency_map.shape
    total_pixels = h * w

    binary_mask = (saliency_map >= settings.tau_pixel).astype(np.uint8)
    active_pixels = int(np.sum(binary_mask))
    saliency_score = active_pixels / total_pixels if total_pixels > 0 else 0.0
    is_active = saliency_score >= settings.tau_anomaly

    logger.info(
        "Stage 1 SOD | tau_pixel=%s | tau_anomaly=%s",
        settings.tau_pixel,
        settings.tau_anomaly,
    )
    logger.info(
        "  Saliency Score: %.6f (%d/%d active pixels)",
        saliency_score,
        active_pixels,
        total_pixels,
    )
    logger.info("  Routing Decision: %s", "ACTIVE_ROUTE" if is_active else "PASS_ROUTE")

    return {
        "is_active": is_active,
        "saliency_score": saliency_score,
        "binary_mask": binary_mask,
        "latency_ms": latency_ms,
        "error": None,
    }
