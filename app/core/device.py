"""Compute-device resolution for inference."""
import logging

logger = logging.getLogger("device")


def resolve_device(requested: str = "auto") -> str:
    """Resolve a requested device string to an actual usable device.

    ``auto`` probes CUDA first, then MPS (Apple Silicon), then falls back
    to CPU. Any explicit request (``cuda``/``mps``/``cpu``) is returned
    as-is so callers can pin a device.
    """
    if requested and requested != "auto":
        return requested
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except Exception:  # pragma: no cover - torch import guard
        logger.exception("Failed to probe accelerator; falling back to CPU")
    return "cpu"
