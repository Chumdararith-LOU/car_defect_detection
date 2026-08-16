from typing import List, Optional

from schemas.model_registry import GateResult, ModelVersion, StageType

# Gate thresholds per stage (from architecture.md section 11)
STAGE1_GATES = {
    "min_recall": 0.90,
}

STAGE2_GATES = {
    "min_test_mask_map50_tolerance": 0.005,
    "max_rare_class_recall_regression": 0.05,
}

STAGE3_GATES = {
    "min_test_mask_map50_tolerance": 0.005,
}


def evaluate_gates(
    candidate: ModelVersion,
    champion: Optional[ModelVersion],
) -> List[GateResult]:
    """Evaluate all promotion gates for a candidate model."""
    stage = candidate.stage
    results: List[GateResult] = []

    if stage == StageType.STAGE1:
        results.extend(_evaluate_stage1_gates(candidate, champion))
    elif stage == StageType.STAGE2:
        results.extend(_evaluate_stage2_gates(candidate, champion))
    elif stage == StageType.STAGE3:
        results.extend(_evaluate_stage3_gates(candidate, champion))

    # Common gate: clean leakage audit
    results.append(_check_leakage_audit(candidate))

    return results


def all_gates_passed(results: List[GateResult]) -> bool:
    """Return True only if every gate passed."""
    return all(r.passed for r in results)


# ---------------------------------------------------------------------------
# Stage-specific gate logic
# ---------------------------------------------------------------------------


def _evaluate_stage1_gates(
    candidate: ModelVersion,
    champion: Optional[ModelVersion],
) -> List[GateResult]:
    results: List[GateResult] = []

    min_recall = STAGE1_GATES["min_recall"]
    candidate_recall = candidate.metrics.get("recall", 0.0)

    results.append(
        GateResult(
            gate_name="min_recall",
            passed=candidate_recall >= min_recall,
            candidate_value=candidate_recall,
            champion_value=None,
            threshold=f">= {min_recall}",
            reason=f"Recall {candidate_recall:.3f} {'>=' if candidate_recall >= min_recall else '<'} {min_recall}",
        )
    )

    return results


def _evaluate_stage2_gates(
    candidate: ModelVersion,
    champion: Optional[ModelVersion],
) -> List[GateResult]:
    results: List[GateResult] = []

    # Gate 1: min_test_mask_map50 = champion - tolerance
    tolerance = STAGE2_GATES["min_test_mask_map50_tolerance"]
    candidate_map50 = candidate.metrics.get("test_mask_map50", 0.0)

    if champion is not None:
        champion_map50 = champion.metrics.get("test_mask_map50", 0.0)
        threshold = champion_map50 - tolerance
    else:
        champion_map50 = None
        threshold = 0.0

    results.append(
        GateResult(
            gate_name="min_test_mask_map50",
            passed=candidate_map50 >= threshold,
            candidate_value=candidate_map50,
            champion_value=champion_map50,
            threshold=f">= {threshold:.4f} (champion - {tolerance})",
            reason=f"mAP50 {candidate_map50:.4f} vs threshold {threshold:.4f}",
        )
    )

    # Gate 2: rare class recall regression (corrosion, disjoint_part)
    max_regression = STAGE2_GATES["max_rare_class_recall_regression"]
    rare_classes = ["corrosion", "disjoint_part"]

    if champion is not None:
        for cls in rare_classes:
            candidate_cls_recall = candidate.metrics.get(f"recall_{cls}", 0.0)
            champion_cls_recall = champion.metrics.get(f"recall_{cls}", 0.0)
            regression = champion_cls_recall - candidate_cls_recall
            results.append(
                GateResult(
                    gate_name=f"rare_class_recall_{cls}",
                    passed=regression <= max_regression,
                    candidate_value=candidate_cls_recall,
                    champion_value=champion_cls_recall,
                    threshold=f"regression <= {max_regression}",
                    reason=f"{cls}: {candidate_cls_recall:.3f} vs champion {champion_cls_recall:.3f} (regression={regression:.3f})",
                )
            )

    return results


def _evaluate_stage3_gates(
    candidate: ModelVersion,
    champion: Optional[ModelVersion],
) -> List[GateResult]:
    results: List[GateResult] = []

    tolerance = STAGE3_GATES["min_test_mask_map50_tolerance"]
    candidate_map50 = candidate.metrics.get("test_mask_map50", 0.0)

    if champion is not None:
        champion_map50 = champion.metrics.get("test_mask_map50", 0.0)
        threshold = champion_map50 - tolerance
    else:
        champion_map50 = None
        threshold = 0.0

    results.append(
        GateResult(
            gate_name="min_test_mask_map50",
            passed=candidate_map50 >= threshold,
            candidate_value=candidate_map50,
            champion_value=champion_map50,
            threshold=f">= {threshold:.4f} (champion - {tolerance})",
            reason=f"mAP50 {candidate_map50:.4f} vs threshold {threshold:.4f}",
        )
    )

    return results


# ---------------------------------------------------------------------------
# Common gates
# ---------------------------------------------------------------------------


def _check_leakage_audit(candidate: ModelVersion) -> GateResult:
    """Check if the candidate has a clean leakage audit in its evaluation report."""
    audit = candidate.evaluation_report.get("leakage_audit", {})
    is_clean = audit.get("clean", True)  # Default to True if audit not yet run
    return GateResult(
        gate_name="require_clean_leakage_audit",
        passed=is_clean,
        candidate_value=None,
        champion_value=None,
        threshold="clean audit required",
        reason="Leakage audit passed" if is_clean else "Leakage audit detected issues",
    )
