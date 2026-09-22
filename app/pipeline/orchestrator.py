"""Pipeline orchestrator: stitches Stage 1-4 with stage toggling and model combos.

Implements the configurable execution model: each stage can be toggled on/off,
Stage 2 can run arbitrary model combinations or a single model, and stage
dependencies are validated (Stage 4 needs Stage 2; crops need Stage 2).
"""
import logging
import uuid
from datetime import datetime, timezone

from app.core.device import resolve_device
from app.core.model_registry import model_registry
from app.pipeline.crops import attach_crops
from app.pipeline.stage1_sod import run_prescreen
from app.pipeline.stage2_defect import run_defect_inference
from app.pipeline.stage3_panel import run_panel_inference
from app.pipeline.stage4_context import (
    assign_defects_to_panels,
    extract_stage1_blobs,
    rescue_unclassified_anomalies,
)
from app.schemas.inspection import (
    Defect,
    ImageDims,
    InspectionPayload,
    Panel,
    PreScreenResult,
)
from app.schemas.pipeline import PipelineSpec

logger = logging.getLogger("orchestrator")


def generate_inspection_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"INSP_{ts}_{uuid.uuid4().hex[:6]}"


def run_pipeline(img_np, spec: PipelineSpec, inspection_id: str = None) -> InspectionPayload:
    """Run the full inspection pipeline per ``spec``. Returns an InspectionPayload."""
    if inspection_id is None:
        inspection_id = generate_inspection_id()

    device = resolve_device(spec.device)
    disabled_stages = []

    binary_mask = None
    prescreen = None
    defects = []
    panels = []
    suppressed = []
    anomalies = []
    blobs = []

    # ---- Stage 1: SOD prescreen (optional gate) ----
    if spec.stage1.enabled:
        try:
            stage1_model = model_registry.get_model("sod_champion", device)
            ps = run_prescreen(img_np, stage1_model, device)
            binary_mask = ps["binary_mask"]
            prescreen = PreScreenResult(
                anomalyDetected=ps["is_active"],
                score=ps["saliency_score"],
                latencyMs=ps["latency_ms"],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Stage 1 failed or unavailable: %s", e)
            disabled_stages.append("stage1")
    else:
        disabled_stages.append("stage1")

    # ---- Stage 2: defect segmentation (core) ----
    if spec.stage2.enabled:
        defects = run_defect_inference(
            img_np,
            inspection_id,
            preset=spec.preset,
            device=device,
            models=spec.stage2.models,
            merge=spec.stage2.merge,
            class_routing=spec.stage2.class_routing,
        )
    else:
        disabled_stages.append("stage2")

    # ---- Stage 3: panel segmentation ----
    if spec.stage3.enabled:
        try:
            stage3_model = model_registry.get_model("panel_champion", device)
            panels = run_panel_inference(stage3_model, img_np, device)
        except Exception as e:  # noqa: BLE001
            logger.warning("Stage 3 failed or unavailable: %s", e)
            disabled_stages.append("stage3")
    else:
        disabled_stages.append("stage3")

    # ---- Stage 4: context mapping (requires Stage 2) ----
    if spec.stage4.enabled:
        if spec.stage2.enabled:
            kept, suppressed_dets = assign_defects_to_panels(defects, panels)
            defects = kept
            suppressed = list(suppressed_dets)
            if binary_mask is not None:
                rescued, suppressed_blobs = rescue_unclassified_anomalies(
                    binary_mask, defects, panels, inspection_id
                )
                anomalies = rescued
                suppressed.extend(suppressed_blobs)
                blobs = extract_stage1_blobs(binary_mask, inspection_id, panels)
        else:
            logger.info("Stage 4 skipped: requires Stage 2 defects.")
            disabled_stages.append("stage4")
    else:
        disabled_stages.append("stage4")

    # ---- Crops (require Stage 2 defects) ----
    if spec.return_crops and defects:
        defects = attach_crops(img_np, defects, inspection_id)

    # ---- Assemble payload ----
    img_h, img_w = img_np.shape[:2]
    defect_models = [Defect(**d) for d in defects]
    panel_models = None
    if panels:
        panel_models = [
            Panel(id=str(p["id"]), label=p["label"], polygon=p["polygon"])
            for p in panels
        ]

    return InspectionPayload(
        inspection_id=inspection_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        vehicle_color_detected="Unknown",
        total_defects_found=len(defect_models),
        inspection_status="FAIL" if defect_models else "PASS",
        imageDims=ImageDims(width=img_w, height=img_h),
        preScreen=prescreen,
        panels=panel_models,
        defects=defect_models,
        unclassified_anomalies=anomalies,
        suppressed_detections=suppressed,
        stage1_blobs=blobs,
        disabled_stages=disabled_stages,
    )
