import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from ultralytics import YOLO

# Reuse the validated Phase 3 SAHI production module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage2" / "inference"))
from sahi_inference import SahiInference, load_config  # noqa: E402

# ---- Constants (from the Technical Brief) ----
THETA_CONTAINMENT = 0.50  # IoD threshold; below => "Boundary/Trim"
PANEL_IMGSZ = 640  # Stage 3 was trained at 640 -> infer at native res


def mask_to_polygons(mask):
    """Convert a binary mask to a list of Shapely Polygons (global coords)."""
    polys = []
    cnts, _ = cv2.findContours(
        mask.astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for c in cnts:
        if c.shape[0] < 3:
            continue
        pts = [(float(x), float(y)) for x, y in c.reshape(-1, 2)]
        p = Polygon(pts)
        if p.is_valid and p.area > 0:
            polys.append(p)
    return polys


def build_panel_unions(panel_result):
    """Build per-class union polygons from the Stage 3 global prediction.

    panel_result.masks.xy[i] is instance i's polygon in original-image coords.
    Multiple instances of the same class are unioned into one region M_i.
    Returns: {class_name: (union_polygon, total_pixel_area)}
    """
    names = panel_result.names
    by_class = {}
    if panel_result.masks is None:
        return by_class

    for i, xy in enumerate(panel_result.masks.xy):
        if len(xy) < 3:
            continue
        cls_id = int(panel_result.boxes.cls[i].item())
        cls_name = names[cls_id]
        poly = Polygon([(float(x), float(y)) for x, y in xy])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or poly.area <= 0:
            continue
        by_class.setdefault(cls_name, []).append(poly)

    unions = {}
    for cls_name, polys in by_class.items():
        u = unary_union(polys)
        if u.is_empty or u.area <= 0:
            continue
        unions[cls_name] = (u, float(u.area))
    return unions


def assign_panel(defect_poly, panel_unions):
    """IoD assignment per the Technical Brief. Returns (panel, iod)."""
    best_panel = "Boundary/Trim"
    best_iod = 0.0
    d_area = defect_poly.area
    if d_area <= 0:
        return best_panel, 0.0
    for panel_name, (panel_poly, _area) in panel_unions.items():
        if not defect_poly.intersects(panel_poly):
            continue
        inter = defect_poly.intersection(panel_poly).area
        iod = inter / d_area
        if iod > best_iod:
            best_iod = iod
            best_panel = panel_name
    if best_iod < THETA_CONTAINMENT:
        return "Boundary/Trim", best_iod
    return best_panel, best_iod


def crop_with_padding(img, bbox, pad=20):
    h, w = img.shape[:2]
    x1 = max(0, bbox[0] - pad)
    y1 = max(0, bbox[1] - pad)
    x2 = min(w, bbox[2] + pad)
    y2 = min(h, bbox[3] + pad)
    return img[y1:y2, x1:x2]


def run_mapping(
    image_path,
    stage2_weights,
    stage3_weights,
    sahi_cfg_path,
    out_dir,
    device_s2,
    device_s3,
    preset_override=None,
    panel_conf=0.25,
):
    image_path = Path(image_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    # --- Stage 3: global panel segmentation ---
    print(f"[Stage 3] Loading panel model: {stage3_weights}")
    panel_model = YOLO(str(stage3_weights))
    panel_res = panel_model.predict(
        source=str(image_path),
        imgsz=PANEL_IMGSZ,
        device=device_s3,
        retina_masks=True,
        verbose=False,
        conf=panel_conf,
    )[0]
    panel_unions = build_panel_unions(panel_res)
    print(
        f"[Stage 3] {len(panel_unions)} panel classes detected: "
        f"{sorted(panel_unions.keys())}"
    )

    # --- Stage 2: tiled defect segmentation (SAHI) ---
    print(f"[Stage 2] Loading SAHI engine: {stage2_weights}")
    cfg = load_config(sahi_cfg_path)
    if preset_override:
        cfg["preset"] = preset_override
    print(f"[Stage 2] Using preset: {cfg['preset']}")
    engine = SahiInference(str(stage2_weights), cfg, device=device_s2)
    defects = engine.predict(str(image_path))
    print(f"[Stage 2] {len(defects)} defects after acceptance + Mask-IOS NMS")

    # --- Stage 4: IoD assignment + DSI + report ---
    report_defects = []
    overlay = img.copy()

    # Draw panel boundaries (green) on the overlay.
    for panel_name, (panel_poly, _area) in panel_unions.items():
        for geom in (
            panel_poly.geoms if panel_poly.geom_type == "MultiPolygon" else [panel_poly]
        ):
            pts = np.array(list(geom.exterior.coords), np.int32).reshape(-1, 1, 2)
            cv2.polylines(overlay, [pts], True, (0, 200, 0), 2)

    for idx, d in enumerate(defects, start=1):
        defect_polys = mask_to_polygons(d["mask"])
        if not defect_polys:
            continue
        defect_poly = unary_union(defect_polys)
        if defect_poly.is_empty or defect_poly.area <= 0:
            continue

        panel, iod = assign_panel(defect_poly, panel_unions)
        dsi = (
            defect_poly.area / panel_unions[panel][1] * 100.0
            if panel in panel_unions
            else 0.0
        )

        defect_id = f"DEF_{idx:03d}"
        crop_path = out_dir / f"{image_path.stem}_{defect_id}.png"
        cv2.imwrite(str(crop_path), crop_with_padding(img, d["bbox"]))

        # Draw defect contour + label on overlay (red).
        for geom in (
            defect_poly.geoms
            if defect_poly.geom_type == "MultiPolygon"
            else [defect_poly]
        ):
            pts = np.array(list(geom.exterior.coords), np.int32).reshape(-1, 1, 2)
            cv2.drawContours(overlay, [pts], -1, (0, 0, 255), 2)
        label = f"{d['name']} -> {panel} (IoD {iod:.2f}, DSI {dsi:.2f}%)"
        cv2.putText(
            overlay,
            label,
            (d["bbox"][0], max(15, d["bbox"][1] - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

        report_defects.append(
            {
                "defect_id": defect_id,
                "class": d["name"],
                "confidence": round(d["score"], 4),
                "global_bbox_xyxy": d["bbox"],
                "metrics": {
                    "pixel_area": round(float(defect_poly.area), 2),
                    "assigned_panel": panel,
                    "containment_ratio_iod": round(iod, 4),
                    "damage_severity_index_dsi": round(dsi, 4),
                },
                "crop_storage_path": str(crop_path),
            }
        )

    overlay_path = out_dir / f"{image_path.stem}_overlay.png"
    cv2.imwrite(str(overlay_path), overlay)

    report = {
        "inspection_id": f"INSP_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_image": str(image_path),
        "total_defects_found": len(report_defects),
        "inspection_status": "FAIL" if report_defects else "PASS",
        "defects": report_defects,
    }
    report_path = out_dir / f"{image_path.stem}_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print(
        f"Inspection: {report['inspection_status']} | "
        f"{len(report_defects)} defect(s)"
    )
    print("=" * 70)
    for rd in report_defects:
        m = rd["metrics"]
        print(
            f"  {rd['defect_id']} {rd['class']:<14} conf={rd['confidence']:.2f} "
            f"-> {m['assigned_panel']:<16} IoD={m['containment_ratio_iod']:.3f} "
            f"DSI={m['damage_severity_index_dsi']:.3f}%"
        )
    print(f"\nOverlay: {overlay_path}")
    print(f"Report:  {report_path}")
    print(f"Crops:   {out_dir}")
    return report


def main():
    ap = argparse.ArgumentParser(description="Stage 4 spatial context mapper")
    ap.add_argument("--image", required=True)
    ap.add_argument(
        "--stage2-weights",
        default="runs/segment/stage1_head_warmup_7cls_extended/"
        "stage1_head_warmup_7cls_extended/weights/best.pt",
    )
    ap.add_argument(
        "--stage3-weights",
        default="mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/"
        "artifacts/weights/best.pt",
    )
    ap.add_argument("--sahi-config", default="configs/inference/sahi_production.yaml")
    ap.add_argument("--out-dir", default="reports/stage4_mapping")
    ap.add_argument(
        "--preset",
        default=None,
        help="Override SAHI preset (balanced/safety/max_recall)",
    )
    ap.add_argument(
        "--panel-conf",
        type=float,
        default=0.25,
        help="Confidence threshold for the Stage 3 panel model",
    )
    ap.add_argument("--device-s2", default="mps")
    ap.add_argument("--device-s3", default="mps")
    a = ap.parse_args()

    run_mapping(
        image_path=a.image,
        stage2_weights=a.stage2_weights,
        stage3_weights=a.stage3_weights,
        sahi_cfg_path=a.sahi_config,
        out_dir=a.out_dir,
        device_s2=a.device_s2,
        device_s3=a.device_s3,
        preset_override=a.preset,
        panel_conf=a.panel_conf,
    )


if __name__ == "__main__":
    main()
