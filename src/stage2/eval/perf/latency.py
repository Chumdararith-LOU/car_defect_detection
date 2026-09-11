"""Inference latency profiling.

Measures wall-clock time for each stage of the inference pipeline:
- Preprocessing (image loading, resizing, normalization)
- Model inference (forward pass)
- Postprocessing (NMS, thresholding, coordinate transformation)

References:
    - eval.md, Module 21: Tiling Parameter Sensitivity (Patch Size vs. Speed)
    - Production constraint: < 500ms per image (48 patches × ~8ms + 50ms NMS)
"""

import time
import numpy as np
from typing import Dict, Callable, Optional
from dataclasses import dataclass


@dataclass
class LatencyResult:
    """Container for latency measurements."""

    preprocess_ms: float = 0.0
    inference_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0
    fps: float = 0.0
    num_runs: int = 0

    def to_dict(self) -> Dict:
        return {
            "preprocess_ms": round(self.preprocess_ms, 2),
            "inference_ms": round(self.inference_ms, 2),
            "postprocess_ms": round(self.postprocess_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "fps": round(self.fps, 2),
            "num_runs": self.num_runs,
        }


class LatencyProfiler:
    """Profile inference latency over multiple runs.

    Usage:
        profiler = LatencyProfiler(warmup_runs=3, measure_runs=10)

        for image in images:
            profiler.start()
            # ... preprocessing ...
            profiler.mark("preprocess")
            # ... inference ...
            profiler.mark("inference")
            # ... postprocessing ...
            profiler.mark("postprocess")
            profiler.end()

        results = profiler.get_results()
    """

    def __init__(self, warmup_runs: int = 3, measure_runs: int = 10):
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs
        self._run_count = 0
        self._current_marks: Dict[str, float] = {}
        self._current_start: float = 0.0
        self._records: list = []

    def start(self):
        """Mark the start of a new measurement run."""
        self._run_count += 1
        self._current_start = time.perf_counter()
        self._current_marks = {}

    def mark(self, stage: str):
        """Mark the end of a pipeline stage.

        Args:
            stage: Stage name ('preprocess', 'inference', 'postprocess')
        """
        self._current_marks[stage] = time.perf_counter()

    def end(self):
        """Mark the end of the current run and record measurements."""
        total_time = time.perf_counter() - self._current_start

        # Skip warmup runs
        if self._run_count <= self.warmup_runs:
            return

        record = {"total": total_time}
        prev_time = self._current_start

        for stage in ["preprocess", "inference", "postprocess"]:
            if stage in self._current_marks:
                stage_time = self._current_marks[stage] - prev_time
                record[stage] = stage_time
                prev_time = self._current_marks[stage]
            else:
                record[stage] = 0.0

        self._records.append(record)

    def get_results(self) -> LatencyResult:
        """Compute aggregate latency statistics."""
        if not self._records:
            return LatencyResult()

        n = len(self._records)
        avg_preprocess = np.mean([r.get("preprocess", 0) for r in self._records]) * 1000
        avg_inference = np.mean([r.get("inference", 0) for r in self._records]) * 1000
        avg_postprocess = (
            np.mean([r.get("postprocess", 0) for r in self._records]) * 1000
        )
        avg_total = np.mean([r["total"] for r in self._records]) * 1000
        fps = 1000.0 / avg_total if avg_total > 0 else 0.0

        return LatencyResult(
            preprocess_ms=avg_preprocess,
            inference_ms=avg_inference,
            postprocess_ms=avg_postprocess,
            total_ms=avg_total,
            fps=fps,
            num_runs=n,
        )


def profile_callable(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[Dict] = None,
    warmup_runs: int = 3,
    measure_runs: int = 10,
) -> LatencyResult:
    """Profile a simple callable (no stage breakdown).

    Args:
        func: The function to profile
        args: Positional arguments
        kwargs: Keyword arguments
        warmup_runs: Number of warmup iterations (not measured)
        measure_runs: Number of measurement iterations

    Returns:
        LatencyResult with total time and FPS
    """
    if kwargs is None:
        kwargs = {}

    # Warmup
    for _ in range(warmup_runs):
        func(*args, **kwargs)

    # Measure
    times = []
    for _ in range(measure_runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg_total = np.mean(times) * 1000
    fps = 1000.0 / avg_total if avg_total > 0 else 0.0

    return LatencyResult(
        total_ms=avg_total,
        fps=fps,
        num_runs=measure_runs,
    )


def format_latency_report(
    results: LatencyResult,
    model_name: str = "Model",
    patch_count: Optional[int] = None,
) -> str:
    """Format latency results as a Markdown table.

    Args:
        results: LatencyResult from profiling
        model_name: Name of the model
        patch_count: Number of SAHI patches (if applicable)

    Returns:
        Markdown-formatted string
    """
    lines = []
    lines.append(f"## Latency Report: {model_name}")
    lines.append("")
    if patch_count:
        lines.append(f"SAHI patch count: {patch_count}")
        lines.append("")
    lines.append("| Stage | Time (ms) |")
    lines.append("|-------|-----------|")
    if results.preprocess_ms > 0:
        lines.append(f"| Preprocess | {results.preprocess_ms:.1f} |")
    if results.inference_ms > 0:
        lines.append(f"| Inference | {results.inference_ms:.1f} |")
    if results.postprocess_ms > 0:
        lines.append(f"| Postprocess/NMS | {results.postprocess_ms:.1f} |")
    lines.append(f"| **Total** | **{results.total_ms:.1f}** |")
    lines.append(f"| FPS | {results.fps:.2f} |")
    lines.append(f"| Runs averaged | {results.num_runs} |")
    lines.append("")

    # Production budget check
    if results.total_ms <= 500:
        lines.append("✅ Within 500ms production budget")
    else:
        lines.append(
            f"⚠️ Exceeds 500ms production budget by {results.total_ms - 500:.1f}ms"
        )

    return "\n".join(lines)
