"""Memory profiling for inference.

Measures peak memory usage during model inference. Supports:
- CUDA: torch.cuda.max_memory_allocated()
- MPS (Apple Silicon): torch.mps.current_allocated_memory()
- CPU: psutil or resource module (approximate)

References:
    - eval.md, Module 6: GPU Memory Wall (290GB VRAM for 4000x3000 activations)
    - eval.md, Module 21: VRAM scales with patch size (320→1x, 640→4x, 1280→16x)
"""

import torch
from typing import Dict, Optional


def get_backend() -> str:
    """Detect the active compute backend."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_peak_memory_mb() -> float:
    """Get peak memory usage in megabytes for the active backend.

    Returns:
        Peak memory in MB. Returns 0.0 if unavailable.
    """
    backend = get_backend()

    try:
        if backend == "cuda":
            torch.cuda.synchronize()
            peak_bytes = torch.cuda.max_memory_allocated()
            return peak_bytes / (1024**2)

        elif backend == "mps":
            # MPS memory tracking (PyTorch >= 2.0)
            if hasattr(torch.mps, "current_allocated_memory"):
                current_bytes = torch.mps.current_allocated_memory()
                return current_bytes / (1024**2)
            return 0.0

        else:
            # CPU fallback: try psutil
            try:
                import psutil
                import os

                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024**2)
            except ImportError:
                return 0.0

    except Exception:
        return 0.0


def reset_memory_stats():
    """Reset memory tracking counters for the active backend."""
    backend = get_backend()

    try:
        if backend == "cuda":
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()
        elif backend == "mps":
            if hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()
    except Exception:
        pass


def profile_memory(
    func,
    args: tuple = (),
    kwargs: Optional[Dict] = None,
) -> Dict:
    """Measure peak memory usage of a function call.

    Args:
        func: The function to profile
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Dict with 'peak_memory_mb', 'backend', and 'success'
    """
    if kwargs is None:
        kwargs = {}

    backend = get_backend()
    reset_memory_stats()

    try:
        func(*args, **kwargs)
        peak_mb = get_peak_memory_mb()

        return {
            "peak_memory_mb": round(peak_mb, 2),
            "backend": backend,
            "success": True,
        }
    except Exception as e:
        return {
            "peak_memory_mb": 0.0,
            "backend": backend,
            "success": False,
            "error": str(e),
        }


def format_memory_report(
    memory_stats: Dict,
    model_name: str = "Model",
    patch_size: Optional[int] = None,
) -> str:
    """Format memory stats as a Markdown report.

    Args:
        memory_stats: Output from profile_memory
        model_name: Name of the model
        patch_size: SAHI patch size (for context)

    Returns:
        Markdown-formatted string
    """
    lines = []
    lines.append(f"## Memory Report: {model_name}")
    lines.append("")
    if patch_size:
        lines.append(f"SAHI patch size: {patch_size}×{patch_size}")
        lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Backend | {memory_stats['backend']} |")
    lines.append(f"| Peak Memory | {memory_stats['peak_memory_mb']:.1f} MB |")
    lines.append(f"| Peak Memory | {memory_stats['peak_memory_mb'] / 1024:.2f} GB |")
    lines.append("")

    if not memory_stats.get("success", True):
        lines.append(
            f"⚠️ Memory profiling failed: {memory_stats.get('error', 'unknown')}"
        )

    return "\n".join(lines)
