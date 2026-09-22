"""Stage 1: Salient Object Detection (SOD) pre-screener.

A lightweight binary model that estimates whether a vehicle image contains any
surface anomaly. It is an optional fast gate before the heavier Stage 2 defect
segmentation and can be toggled off entirely via the pipeline spec.
"""
import logging
import time

import cv2
import numpy as np

logger = logging.getLogger("stage1_sod")

# Saliency thresholds: a pixel is "active" if its saliency >= TAU_PIXEL; the frame
# is routed as an anomaly if the active-pixel fraction >= TAU_ANOMALY.
TAU_PIXEL = 0.70
TAU_ANOMALY = 0.0005


def run_prescreen(img_np: np.ndarray, model, device: str = "cpu") -> dict:
    """Run the Stage 1 SOD model and compute saliency metrics.

    Returns a dict with the fields the orchestrator needs:
    ``is_active``, ``saliency_score``, ``binary_mask``, ``latency_ms``, ``error``.
    """
    start_time = time.time()
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    results = model(img_bgr, device=device, verbose=False)
    result = results[0]
    latency_ms = (time.time() - start_time) * 1000.0

    # Fallback if the model does not expose a semantic mask.
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
    binary_mask = (saliency_map >= TAU_PIXEL).astype(np.uint8)
    active_pixels = int(np.sum(binary_mask))
    saliency_score = active_pixels / total_pixels if total_pixels > 0 else 0.0
    is_active = saliency_score >= TAU_ANOMALY

    logger.info(
        "Stage1 SOD | tau_pixel=%s tau_anomaly=%s score=%.6f active=%d/%d -> %s",
        TAU_PIXEL,
        TAU_ANOMALY,
        saliency_score,
        active_pixels,
        total_pixels,
        "ACTIVE" if is_active else "PASS",
    )

    return {
        "is_active": is_active,
        "saliency_score": saliency_score,
        "binary_mask": binary_mask,
        "latency_ms": latency_ms,
        "error": None,
    }
