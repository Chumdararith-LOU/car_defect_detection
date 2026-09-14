#!/usr/bin/env python3
"""
Corrosion / scratch / crack inference-threshold sweep.

Run on server:
  conda activate car_defect
  python src/analysis/threshold_sweep.py

Method: one inference pass per image set at conf=0.001; thresholds are then
applied in post-hoc. This is EXACTLY equivalent to re-running predict() at
each threshold: NMS is greedy in descending confidence, so a box with
conf >= T can only be suppressed by boxes with conf >= T, which are present
in both runs. No approximation.

Outputs:
  reports/threshold_sweep_results.md
  reports/threshold_sweep_corrosion.csv
  reports/threshold_sweep_clean.csv
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
for _p in (_PROJECT_ROOT, _VENDOR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ultralytics import YOLO

CLASS_NAMES = {
    0: "broken_lamp",
    1: "corrosion",
    2: "crack",
    3: "dent",
    4: "disjoint_part",
    5: "glass_shatter",
    6: "scratch",
}
CORROSION, CRACK, SCRATCH = 1, 2, 6
N_CLASSES = 7

MODEL_PATHS = [
    "runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt",
    "runs/segment/runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt",
]
TEST_DIR = "data/processed/yolo_seg/images/test"
TEST_LABELS_DIR = "data/processed/yolo_seg/labels/test"
CLEAN_DIR = "data/processed/clean_cars/images/clean_eval"
REPORT_MD = "reports/threshold_sweep_results.md"
REPORT_CORROSION_CSV = "reports/threshold_sweep_corrosion.csv"
REPORT_CLEAN_CSV = "reports/threshold_sweep_clean.csv"

CORROSION_THRESHOLDS = [0.01, 0.02, 0.03, 0.04, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25]
SCRATCH_THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30]
CRACK_THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30]
DEFAULT_CONF = 0.25
MATCH_IOU = 0.5
CLEAN_FPR_LIMIT = 30.0
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def resolve_model_path():
    for p in MODEL_PATHS:
        if os.path.exists(p):
            return p
    sys.exit("ERROR: model not found. Tried:\n" + "\n".join(MODEL_PATHS))


def list_images(images_dir):
    d = Path(images_dir)
    if not d.is_dir():
        sys.exit(f"ERROR: image directory not found: {images_dir}")
    files = [p for p in sorted(d.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    if not files:
        sys.exit(f"ERROR: no images found in {images_dir}")
    return files


def load_ground_truths(labels_dir, image_paths):
    """image_name -> list of {class_id, bbox (normalized), polygon}."""
    gts_by_image = {}
    for img_path in image_paths:
        label_path = Path(labels_dir) / (img_path.stem + ".txt")
        gts = []
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 7:
                        continue
                    class_id = int(parts[0])
                    coords = [float(x) for x in parts[1:]]
                    if len(coords) % 2:
                        continue
                    xs, ys = coords[0::2], coords[1::2]
                    gts.append({
                        "class_id": class_id,
                        "bbox": (min(xs), min(ys), max(xs), max(ys)),
                        "polygon": list(zip(xs, ys)),
                    })
        gts_by_image[img_path.name] = gts
    return gts_by_image


def compute_iou(b1, b2):
    x1, y1 = max(b1[0], b2[0]), max(b1[1], b2[1])
    x2, y2 = min(b1[2], b2[2]), min(b1[3], b2[3])
    if x1 >= x2 or y1 >= y2:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0.0


def rasterize_polygon(poly_norm, w, h):
    pts = np.array([(x * w, y * h) for x, y in poly_norm], dtype=np.int32)
    m = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(m, [pts], 1)
    return m.astype(bool)


def process_test_image(model, img_path, gts):
    """One inference; returns per-class record with precomputed IoU matrices.

    rec[c] = {preds: [(conf, bbox_px)], gts: [bbox_px],
              bbox_iou: (P,G) float32, mask_iou: (P,G) float32}
    """
    res = model.predict(str(img_path), conf=0.001, iou=0.7, imgsz=1024, verbose=False)[0]
    h, w = res.orig_shape
    rec: dict = {c: {"preds": [], "gts": []} for c in range(N_CLASSES)}
    for gt in gts:
        rec[gt["class_id"]]["gts"].append(
            (gt["bbox"][0] * w, gt["bbox"][1] * h, gt["bbox"][2] * w, gt["bbox"][3] * h))

    if res.boxes is not None and len(res.boxes):
        xyxy = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        cls = res.boxes.cls.cpu().numpy().astype(int)
        masks = res.masks.data.cpu().numpy().astype(bool) if res.masks is not None else None
        for j in range(len(xyxy)):
            c = int(cls[j])
            rec[c]["preds"].append((float(confs[j]), xyxy[j].tolist()))
            if masks is not None:
                m = masks[j]
                if m.shape[:2] != (h, w):  # vendor ultralytics may return masks at inference res
                    m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
                rec[c].setdefault("pred_masks", []).append(m)

    for c in range(N_CLASSES):
        preds, gts_c = rec[c]["preds"], rec[c]["gts"]
        P, G = len(preds), len(gts_c)
        if P == 0 or G == 0:
            rec[c].pop("pred_masks", None)
            continue
        bbox_iou = np.zeros((P, G), dtype=np.float32)
        for i, (_, pb) in enumerate(preds):
            for g, gb in enumerate(gts_c):
                bbox_iou[i, g] = compute_iou(pb, gb)
        mask_iou = np.zeros((P, G), dtype=np.float32)
        pred_masks = rec[c].get("pred_masks")
        if pred_masks is not None:
            gt_masks = [rasterize_polygon(gt["polygon"], w, h) for gt in gts if gt["class_id"] == c]
            pred_areas = [m.sum() for m in pred_masks]
            gt_areas = [m.sum() for m in gt_masks]
            for i in range(P):
                for g in range(G):
                    if bbox_iou[i, g] > 0:  # mask IoU is 0 whenever bboxes are disjoint
                        inter = int(np.logical_and(pred_masks[i], gt_masks[g]).sum())
                        if inter > 0:
                            mask_iou[i, g] = inter / (pred_areas[i] + gt_areas[g] - inter)
        rec[c]["bbox_iou"] = bbox_iou
        rec[c]["mask_iou"] = mask_iou
        rec[c].pop("pred_masks", None)
    return rec


def process_clean_image(model, img_path):
    """Return list of corrosion prediction confidences (all, conf=0.001)."""
    res = model.predict(str(img_path), conf=0.001, iou=0.7, imgsz=1024, verbose=False)[0]
    confs = []
    if res.boxes is not None and len(res.boxes):
        cls = res.boxes.cls.cpu().numpy().astype(int)
        confs_arr = res.boxes.conf.cpu().numpy()
        for j in range(len(cls)):
            if int(cls[j]) == CORROSION:
                confs.append(float(confs_arr[j]))
    return confs


def greedy_match(kept_indices, iou_matrix, n_gt):
    """Conf-desc greedy matching at IoU >= MATCH_IOU. Returns TP flags (1.0/0.0)."""
    matched = [False] * n_gt
    flags = []
    for i in kept_indices:
        row = iou_matrix[i]
        best_g, best_v = -1, 0.0
        for g in range(n_gt):
            if not matched[g] and row[g] >= MATCH_IOU and row[g] > best_v:
                best_g, best_v = g, row[g]
        if best_g >= 0:
            matched[best_g] = True
            flags.append(1.0)
        else:
            flags.append(0.0)
    return flags


def class_pr_curve(per_image, c, threshold, use_mask):
    """Pooled (conf-desc TP flags, total GT count) for class c at a threshold."""
    flags = []
    n_gt = 0
    for rec in per_image.values():
        d = rec[c]
        gts_n = len(d["gts"])
        n_gt += gts_n
        if not d["preds"] or gts_n == 0:
            continue
        kept = sorted((i for i in range(len(d["preds"])) if d["preds"][i][0] >= threshold),
                      key=lambda i: -d["preds"][i][0])
        mat = d["mask_iou"] if use_mask else d["bbox_iou"]
        flags.extend(greedy_match(kept, mat, gts_n))
    return flags, n_gt


def voc_ap11(flags, n_gt):
    if n_gt == 0 or not flags:
        return 0.0
    tp = np.array(flags)
    tp_cum, fp_cum = np.cumsum(tp), np.cumsum(1.0 - tp)
    recall = tp_cum / n_gt
    precision = tp_cum / (tp_cum + fp_cum)
    ap = 0.0
    for t in [i / 10 for i in range(11)]:
        idx = np.where(recall >= t)[0]
        if len(idx):
            ap += precision[idx].max()
    return ap / 11.0


def prf1(flags, n_gt):
    tp = int(sum(flags))
    fp = len(flags) - tp
    fn = n_gt - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / n_gt if n_gt else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, tp, fp, fn


def overall_mask_map50(per_image, corrosion_threshold):
    aps = []
    for c in range(N_CLASSES):
        thr = corrosion_threshold if c == CORROSION else DEFAULT_CONF
        flags, n_gt = class_pr_curve(per_image, c, thr, use_mask=True)
        if n_gt > 0:
            aps.append(voc_ap11(flags, n_gt))
    return float(np.mean(aps)) if aps else 0.0


def clean_metrics(clean_confs, threshold):
    fp_images = 0
    total_fps = 0
    kept_confs = []
    for confs in clean_confs:
        kept = [c for c in confs if c >= threshold]
        if kept:
            fp_images += 1
            total_fps += len(kept)
            kept_confs.extend(kept)
    fpr = 100.0 * fp_images / len(clean_confs) if clean_confs else 0.0
    mean_conf = float(np.mean(kept_confs)) if kept_confs else None
    return fpr, total_fps, mean_conf


def main():
    print("=" * 80)
    print("THRESHOLD SWEEP")
    print("=" * 80)

    model_path = resolve_model_path()
    print(f"[*] Model: {model_path}")
    model = YOLO(model_path)

    test_paths = list_images(TEST_DIR)
    clean_paths = list_images(CLEAN_DIR)
    print(f"[*] Test images: {len(test_paths)} | Clean eval images: {len(clean_paths)}")
    gts_by_image = load_ground_truths(TEST_LABELS_DIR, test_paths)

    print("[*] Pass 1: test set inference (conf=0.001, with masks)...")
    test_data = {}
    for i, p in enumerate(test_paths):
        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{len(test_paths)}] {p.name}")
        test_data[p.name] = process_test_image(model, p, gts_by_image[p.name])

    print("[*] Pass 2: clean eval set inference (conf=0.001, boxes only)...")
    clean_confs = []
    for i, p in enumerate(clean_paths):
        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{len(clean_paths)}] {p.name}")
        clean_confs.append(process_clean_image(model, p))

    print("[*] Sweeping corrosion thresholds...")
    corr_rows = []
    for t in CORROSION_THRESHOLDS:
        flags, n_gt = class_pr_curve(test_data, CORROSION, t, use_mask=False)
        precision, recall, f1, tp, fp, fn = prf1(flags, n_gt)
        map50 = overall_mask_map50(test_data, t)
        fpr, total_fps, mean_conf = clean_metrics(clean_confs, t)
        corr_rows.append({
            "threshold": t, "recall": recall, "precision": precision, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "mask_map50": map50,
            "clean_fpr_pct": fpr, "total_clean_fps": total_fps,
            "mean_clean_fp_conf": mean_conf,
        })
        print(f"  T={t:.2f}  R={recall:.3f} P={precision:.3f} F1={f1:.3f} "
              f"mAP50={map50:.3f}  cleanFPR={fpr:.1f}% cleanFPs={total_fps}")

    print("[*] Sweeping scratch thresholds...")
    scratch_rows = []
    for t in SCRATCH_THRESHOLDS:
        flags, n_gt = class_pr_curve(test_data, SCRATCH, t, use_mask=False)
        precision, recall, f1, tp, fp, fn = prf1(flags, n_gt)
        scratch_rows.append({"threshold": t, "recall": recall, "precision": precision,
                             "f1": f1, "tp": tp, "fp": fp, "fn": fn})
        print(f"  T={t:.2f}  R={recall:.3f} P={precision:.3f} F1={f1:.3f}")

    print("[*] Sweeping crack thresholds...")
    crack_rows = []
    for t in CRACK_THRESHOLDS:
        flags, n_gt = class_pr_curve(test_data, CRACK, t, use_mask=False)
        precision, recall, f1, tp, fp, fn = prf1(flags, n_gt)
        crack_rows.append({"threshold": t, "recall": recall, "precision": precision,
                           "f1": f1, "tp": tp, "fp": fp, "fn": fn})
        print(f"  T={t:.2f}  R={recall:.3f} P={precision:.3f} F1={f1:.3f}")

    # Recommendations
    eligible = [r for r in corr_rows if r["clean_fpr_pct"] <= CLEAN_FPR_LIMIT]
    if eligible:
        best_corr = max(eligible, key=lambda r: r["f1"])
        corr_note = f"maximizes F1 subject to Clean FPR <= {CLEAN_FPR_LIMIT:.0f}%"
    else:
        best_corr = min(corr_rows, key=lambda r: r["clean_fpr_pct"])
        corr_note = (f"NO threshold keeps Clean FPR <= {CLEAN_FPR_LIMIT:.0f}%; "
                     f"falling back to lowest Clean FPR")
    best_scratch = max(scratch_rows, key=lambda r: r["f1"])
    best_crack = max(crack_rows, key=lambda r: r["f1"])

    # Report
    L = []
    L.append("# Threshold Sweep Results\n")
    L.append(f"- **Checkpoint:** `{model_path}`")
    L.append(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L.append(f"- **Test set:** {len(test_paths)} images | **Clean eval set:** {len(clean_paths)} images")
    L.append("- **Method:** single inference pass per image at conf=0.001; thresholds applied in "
             "post-hoc (exactly equivalent to per-threshold predict() runs — NMS only suppresses "
             "lower-confidence boxes).")
    L.append(f"- **Corrosion P/R/F1:** bbox IoU >= {MATCH_IOU} (consistent with the corrosion error "
             f"analysis). **Mask mAP50:** mask IoU >= {MATCH_IOU}, 11-point VOC AP, averaged over "
             f"classes with GTs; non-corrosion classes held at conf {DEFAULT_CONF}.\n")

    L.append("## Table 1 — Corrosion threshold sweep\n")
    L.append("| Threshold | Recall | Precision | F1 | TP | FP | FN | Clean FPR (%) | Total Clean FPs | Mean Clean FP Conf | Mask mAP50 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in corr_rows:
        mc = f"{r['mean_clean_fp_conf']:.4f}" if r["mean_clean_fp_conf"] is not None else "N/A"
        L.append(f"| {r['threshold']:.2f} | {r['recall']:.4f} | {r['precision']:.4f} | {r['f1']:.4f} "
                 f"| {r['tp']} | {r['fp']} | {r['fn']} | {r['clean_fpr_pct']:.1f} "
                 f"| {r['total_clean_fps']} | {mc} | {r['mask_map50']:.4f} |")
    L.append("")

    L.append("## Table 2 — Scratch threshold sweep\n")
    L.append("| Threshold | Recall | Precision | F1 |")
    L.append("|---|---|---|---|")
    for r in scratch_rows:
        L.append(f"| {r['threshold']:.2f} | {r['recall']:.4f} | {r['precision']:.4f} | {r['f1']:.4f} |")
    L.append("")

    L.append("## Table 3 — Crack threshold sweep\n")
    L.append("| Threshold | Recall | Precision | F1 |")
    L.append("|---|---|---|---|")
    for r in crack_rows:
        L.append(f"| {r['threshold']:.2f} | {r['recall']:.4f} | {r['precision']:.4f} | {r['f1']:.4f} |")
    L.append("")

    L.append("## Recommendation\n")
    L.append(f"- **Best corrosion threshold: {best_corr['threshold']:.2f}** "
             f"(F1={best_corr['f1']:.4f}, Recall={best_corr['recall']:.4f}, "
             f"Precision={best_corr['precision']:.4f}, Clean FPR={best_corr['clean_fpr_pct']:.1f}%, "
             f"Mask mAP50={best_corr['mask_map50']:.4f}) — {corr_note}")
    L.append(f"- **Best scratch threshold: {best_scratch['threshold']:.2f}** "
             f"(F1={best_scratch['f1']:.4f}, Recall={best_scratch['recall']:.4f}, "
             f"Precision={best_scratch['precision']:.4f}) — maximizes F1")
    L.append(f"- **Best crack threshold: {best_crack['threshold']:.2f}** "
             f"(F1={best_crack['f1']:.4f}, Recall={best_crack['recall']:.4f}, "
             f"Precision={best_crack['precision']:.4f}) — maximizes F1")
    L.append("")

    report_path = Path(REPORT_MD)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(L))

    with open(REPORT_CORROSION_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "recall", "precision", "f1", "tp", "fp", "fn",
                    "mask_map50", "clean_fpr_pct", "total_clean_fps", "mean_clean_fp_conf"])
        for r in corr_rows:
            mc = f"{r['mean_clean_fp_conf']:.4f}" if r["mean_clean_fp_conf"] is not None else ""
            w.writerow([f"{r['threshold']:.2f}", f"{r['recall']:.4f}", f"{r['precision']:.4f}",
                        f"{r['f1']:.4f}", r["tp"], r["fp"], r["fn"], f"{r['mask_map50']:.4f}",
                        f"{r['clean_fpr_pct']:.2f}", r["total_clean_fps"], mc])

    with open(REPORT_CLEAN_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "clean_fpr_pct", "total_clean_fps", "mean_clean_fp_conf"])
        for r in corr_rows:
            mc = f"{r['mean_clean_fp_conf']:.4f}" if r["mean_clean_fp_conf"] is not None else ""
            w.writerow([f"{r['threshold']:.2f}", f"{r['clean_fpr_pct']:.2f}",
                        r["total_clean_fps"], mc])

    if not report_path.exists() or report_path.stat().st_size == 0:
        sys.exit("ERROR: report file missing or empty")

    print(f"\nTHRESHOLD SWEEP COMPLETE — check {REPORT_MD}")


if __name__ == "__main__":
    main()
