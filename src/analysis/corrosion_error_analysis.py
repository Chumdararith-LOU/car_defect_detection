#!/usr/bin/env python3
"""
Corrosion FN/FP Error Analysis

Run on server:
  conda activate car_defect
  python src/analysis/corrosion_error_analysis.py

Outputs (all under reports/corrosion_error_analysis/):
  summary.md, fn_records.csv, fp_records.csv, summary_stats.csv,
  fn_*.png, fp_*.png, background_fps/*.png, class_confusion/*.png
"""

import csv
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

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
CORROSION = 1

MODEL_PATHS = [
    "runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt",
    "runs/segment/runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt",
]
IMAGES_DIR = "data/processed/yolo_seg/images/test"
LABELS_DIR = "data/processed/yolo_seg/labels/test"
OUTPUT_DIR = "reports/corrosion_error_analysis"
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
    return [p for p in sorted(d.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]


def load_ground_truths(labels_dir, image_paths):
    """image_name -> list of {class_id, bbox (normalized), polygon, image_name}."""
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
                        "image_name": img_path.name,
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


def run_inference(model, image_paths, keep_masks=False):
    """image_name -> list of {class_id, confidence, bbox (px), [mask]}."""
    results = {}
    total = len(image_paths)
    for i, img_path in enumerate(image_paths):
        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{total}] {img_path.name}")
        res = model.predict(str(img_path), conf=0.001, iou=0.7, imgsz=1024, verbose=False)[0]
        preds = []
        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy().astype(int)
            masks = res.masks.data.cpu().numpy() if (keep_masks and res.masks is not None) else None
            for j in range(len(xyxy)):
                pred = {
                    "class_id": int(cls[j]),
                    "confidence": float(confs[j]),
                    "bbox": xyxy[j].tolist(),
                }
                if masks is not None:
                    pred["mask"] = masks[j]
                preds.append(pred)
        results[img_path.name] = preds
    return results


def categorize_corrosion_errors(image_name, gts, preds, img_w, img_h):
    """Return (fn_records, fp_records). fn_records also contains 'tp' rows."""
    corrosion_gts = [gt for gt in gts if gt["class_id"] == CORROSION]
    corrosion_preds = [p for p in preds if p["class_id"] == CORROSION]
    gt_bboxes_px = [
        (gt["bbox"][0] * img_w, gt["bbox"][1] * img_h, gt["bbox"][2] * img_w, gt["bbox"][3] * img_h)
        for gt in corrosion_gts
    ]

    # Greedy TP matching at IoU >= 0.5 (best IoU first, tie-break on confidence)
    pairs = []
    for gi, gt_bbox in enumerate(gt_bboxes_px):
        for pi, pred in enumerate(corrosion_preds):
            iou = compute_iou(gt_bbox, pred["bbox"])
            if iou >= 0.5:
                pairs.append((iou, pred["confidence"], gi, pi))
    pairs.sort(reverse=True)
    tp_gt, tp_pred = {}, {}
    for iou, conf, gi, pi in pairs:
        if gi in tp_gt or pi in tp_pred:
            continue
        tp_gt[gi] = (iou, conf)
        tp_pred[pi] = gi

    fn_records = []
    used_preds = set(tp_pred)
    for gi, gt in enumerate(corrosion_gts):
        gt_bbox = gt_bboxes_px[gi]
        w, h = gt_bbox[2] - gt_bbox[0], gt_bbox[3] - gt_bbox[1]
        gt_area_pct = 100.0 * w * h / (img_w * img_h)
        gt_aspect = w / h if h > 0 else 1.0
        overlapping_class = -1

        if gi in tp_gt:
            iou, conf = tp_gt[gi]
            category = "tp" if conf >= 0.25 else "low_confidence"
        else:
            best_iou, best_pi, conf = 0.0, None, 0.0
            for pi, pred in enumerate(corrosion_preds):
                iou = compute_iou(gt_bbox, pred["bbox"])
                if iou > best_iou:
                    best_iou, best_pi, conf = iou, pi, pred["confidence"]
            iou = best_iou
            if best_iou >= 0.3:
                category = "mislocalized"
                if best_pi is not None:
                    used_preds.add(best_pi)
            else:
                best_other_iou = 0.0
                for pred in preds:
                    if pred["class_id"] == CORROSION:
                        continue
                    oi = compute_iou(gt_bbox, pred["bbox"])
                    if oi >= 0.3 and oi > best_other_iou:
                        best_other_iou = oi
                        overlapping_class = pred["class_id"]
                category = "class_confusion" if overlapping_class >= 0 else "completely_missed"

        fn_records.append({
            "image_name": image_name,
            "category": category,
            "gt_area_pct": gt_area_pct,
            "gt_aspect_ratio": gt_aspect,
            "best_iou": iou,
            "best_conf": conf,
            "overlapping_class": overlapping_class,
            "_gt": gt,
            "_gt_bbox_px": gt_bbox,
        })

    fp_records = []
    for pi, pred in enumerate(corrosion_preds):
        if pi in used_preds:
            continue
        pb = pred["bbox"]
        pred_area_pct = 100.0 * (pb[2] - pb[0]) * (pb[3] - pb[1]) / (img_w * img_h)
        best_iou, best_gt_class = 0.0, -1
        for gt in gts:
            gt_bbox = (gt["bbox"][0] * img_w, gt["bbox"][1] * img_h,
                       gt["bbox"][2] * img_w, gt["bbox"][3] * img_h)
            iou = compute_iou(pb, gt_bbox)
            if iou > best_iou:
                best_iou, best_gt_class = iou, gt["class_id"]
        if best_iou < 0.1:
            category = "background_fp"
        elif best_gt_class == CORROSION:
            category = "duplicate" if best_iou >= 0.5 else "localization_error"
        else:
            category = "class_confusion_fp"
        fp_records.append({
            "image_name": image_name,
            "category": category,
            "pred_conf": pred["confidence"],
            "pred_area_pct": pred_area_pct,
            "overlapping_gt_class": best_gt_class,
            "iou_with_gt": best_iou,
            "_pred": pred,
        })

    return fn_records, fp_records


def cross_class_stats(gts, preds, img_w, img_h):
    """Per-class TP/FP/FN at IoU=0.5 (greedy, confidence-ordered)."""
    stats = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CLASS_NAMES}
    for c in CLASS_NAMES:
        gts_c = [gt for gt in gts if gt["class_id"] == c]
        gts_px = [(gt["bbox"][0] * img_w, gt["bbox"][1] * img_h,
                   gt["bbox"][2] * img_w, gt["bbox"][3] * img_h) for gt in gts_c]
        matched = set()
        for pred in sorted((p for p in preds if p["class_id"] == c), key=lambda p: -p["confidence"]):
            best_iou, best_gi = 0.0, None
            for gi, gt_bbox in enumerate(gts_px):
                if gi in matched:
                    continue
                iou = compute_iou(gt_bbox, pred["bbox"])
                if iou >= 0.5 and iou > best_iou:
                    best_iou, best_gi = iou, gi
            if best_gi is not None:
                matched.add(best_gi)
                stats[c]["tp"] += 1
            else:
                stats[c]["fp"] += 1
        stats[c]["fn"] = len(gts_c) - len(matched)
    return stats


def compute_map50(per_image):
    """Pooled VOC-style AP at IoU=0.5 (11-point interpolation).

    per_image: list of (gt_bboxes_px, corrosion_preds) per image.
    """
    n_gt = 0
    flags = []
    for gts_px, preds in per_image:
        n_gt += len(gts_px)
        matched = set()
        for pred in sorted(preds, key=lambda p: -p["confidence"]):
            best_iou, best_gi = 0.0, None
            for gi, gt_bbox in enumerate(gts_px):
                if gi in matched:
                    continue
                iou = compute_iou(gt_bbox, pred["bbox"])
                if iou >= 0.5 and iou > best_iou:
                    best_iou, best_gi = iou, gi
            if best_gi is not None:
                matched.add(best_gi)
                flags.append((pred["confidence"], 1.0))
            else:
                flags.append((pred["confidence"], 0.0))
    if n_gt == 0 or not flags:
        return 0.0
    flags.sort(key=lambda x: -x[0])
    tp = np.array([f[1] for f in flags])
    fp = 1.0 - tp
    tp_cum, fp_cum = np.cumsum(tp), np.cumsum(fp)
    recall = tp_cum / n_gt
    precision = tp_cum / (tp_cum + fp_cum)
    ap = 0.0
    for t in [i / 10 for i in range(11)]:
        idx = np.where(recall >= t)[0]
        if len(idx):
            ap += precision[idx].max()
    return ap / 11.0


def _size_stats(values):
    if not values:
        return None
    a = np.array(values, dtype=float)
    return (float(np.mean(a)), float(np.median(a)), float(np.min(a)), float(np.max(a)))


def _mean(values):
    return float(np.mean(values)) if values else None


def build_stats(fn_records, fp_records, map50, cross):
    tp_recs = [r for r in fn_records if r["category"] == "tp"]
    fn_recs = [r for r in fn_records if r["category"] != "tp"]
    tp_n, fn_n, fp_n = len(tp_recs), len(fn_recs), len(fp_records)
    precision = tp_n / (tp_n + fp_n) if (tp_n + fp_n) else 0.0
    recall = tp_n / (tp_n + fn_n) if (tp_n + fn_n) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    fn_cats = Counter(r["category"] for r in fn_recs)
    fp_cats = Counter(r["category"] for r in fp_records)

    return {
        "precision": precision, "recall": recall, "f1": f1, "map50": map50,
        "tp": tp_n, "fn": fn_n, "fp": fp_n,
        "fn_cats": dict(fn_cats), "fp_cats": dict(fp_cats),
        "tp_areas": _size_stats([r["gt_area_pct"] for r in tp_recs]),
        "fn_areas": _size_stats([r["gt_area_pct"] for r in fn_recs]),
        "fp_areas": _size_stats([r["pred_area_pct"] for r in fp_records]),
        "tp_conf": _mean([r["best_conf"] for r in tp_recs]),
        "fp_conf": _mean([r["pred_conf"] for r in fp_records]),
        "lowconf_fn_conf": _mean([r["best_conf"] for r in fn_recs if r["category"] == "low_confidence"]),
        "bg_fp_conf": _mean([r["pred_conf"] for r in fp_records if r["category"] == "background_fp"]),
        "scratch_confusion_fn": sum(
            1 for r in fn_recs if r["category"] == "class_confusion" and r["overlapping_class"] == 6),
        "fn_confused_as": dict(Counter(
            r["overlapping_class"] for r in fn_recs if r["category"] == "class_confusion")),
        "fp_over": dict(Counter(
            r["overlapping_gt_class"] for r in fp_records if r["category"] == "class_confusion_fp")),
        "cross": cross,
    }


def _overlay_mask(arr, mask, color, alpha=0.5):
    m = np.asarray(mask) > 0.5
    if m.shape != arr.shape[:2]:
        m = np.array(Image.fromarray((m.astype(np.uint8)) * 255).resize(
            (arr.shape[1], arr.shape[0]))) > 127
    arr[m] = arr[m] * (1 - alpha) + np.array(color, dtype=float) * alpha


def draw_fn_example(img_path, gt, out_path, confusion_pred=None):
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon([(x * w, y * h) for x, y in gt["polygon"]], fill=(0, 255, 0, 100))
    od.rectangle([int(gt["bbox"][0] * w), int(gt["bbox"][1] * h),
                  int(gt["bbox"][2] * w), int(gt["bbox"][3] * h)], outline=(0, 255, 0), width=3)
    if confusion_pred is not None:
        od.rectangle([int(v) for v in confusion_pred["bbox"]], outline=(0, 0, 255), width=3)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(out_path)


def draw_fp_example(img_path, pred, out_path):
    img = Image.open(img_path).convert("RGB")
    if "mask" in pred:
        arr = np.array(img)
        _overlay_mask(arr, pred["mask"], (255, 0, 0))
        img = Image.fromarray(arr)
    od = ImageDraw.Draw(img)
    od.rectangle([int(v) for v in pred["bbox"]], outline=(255, 0, 0), width=3)
    img.save(out_path)


def _find_confusing_pred(preds, gt_bbox_px, cls_id):
    best, best_iou = None, 0.0
    for p in preds:
        if p["class_id"] != cls_id:
            continue
        iou = compute_iou(gt_bbox_px, p["bbox"])
        if iou >= 0.3 and iou > best_iou:
            best, best_iou = p, iou
    return best


def save_examples(image_paths_by_name, preds_by_image, fn_records, fp_records, out_dir):
    (out_dir / "background_fps").mkdir(parents=True, exist_ok=True)
    (out_dir / "class_confusion").mkdir(parents=True, exist_ok=True)
    saved = []

    fns = sorted((r for r in fn_records if r["category"] != "tp"), key=lambda r: -r["gt_area_pct"])
    for rank, rec in enumerate(fns[:30], 1):
        name = rec["image_name"]
        confusion = None
        if rec["category"] == "class_confusion":
            confusion = _find_confusing_pred(preds_by_image[name], rec["_gt_bbox_px"], rec["overlapping_class"])
        out = out_dir / f"fn_{rank:02d}_{rec['category']}_{name}"
        draw_fn_example(image_paths_by_name[name], rec["_gt"], out, confusion)
        saved.append(str(out))

    fps = sorted(fp_records, key=lambda r: -r["pred_conf"])
    for rank, rec in enumerate(fps[:30], 1):
        out = out_dir / f"fp_{rank:02d}_{rec['category']}_{rec['image_name']}"
        draw_fp_example(image_paths_by_name[rec["image_name"]], rec["_pred"], out)
        saved.append(str(out))

    bg = sorted((r for r in fp_records if r["category"] == "background_fp"), key=lambda r: -r["pred_conf"])
    for rank, rec in enumerate(bg[:15], 1):
        out = out_dir / "background_fps" / f"fp_{rank:02d}_{rec['image_name']}"
        draw_fp_example(image_paths_by_name[rec["image_name"]], rec["_pred"], out)
        saved.append(str(out))

    cc = sorted((r for r in fn_records if r["category"] == "class_confusion"), key=lambda r: -r["gt_area_pct"])
    for rank, rec in enumerate(cc[:15], 1):
        name = rec["image_name"]
        confusion = _find_confusing_pred(preds_by_image[name], rec["_gt_bbox_px"], rec["overlapping_class"])
        out = out_dir / "class_confusion" / f"fn_{rank:02d}_{name}"
        draw_fn_example(image_paths_by_name[name], rec["_gt"], out, confusion)
        saved.append(str(out))

    return saved


def generate_report(model_path, test_count, stats, saved_files, out_dir):
    L = []
    L.append("# Corrosion Error Analysis Report\n")
    L.append(f"- **Checkpoint:** `{model_path}`")
    L.append(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L.append(f"- **Test set size:** {test_count} images\n")

    L.append("## Overall Metrics (corrosion, IoU=0.5)\n")
    L.append("| Metric | Value |")
    L.append("|---|---|")
    L.append(f"| Precision | {stats['precision']:.4f} |")
    L.append(f"| Recall | {stats['recall']:.4f} |")
    L.append(f"| F1 | {stats['f1']:.4f} |")
    L.append(f"| mAP50 | {stats['map50']:.4f} |")
    L.append(f"| TP / FN / FP | {stats['tp']} / {stats['fn']} / {stats['fp']} |\n")

    L.append("## FN Categories\n")
    L.append("| Category | Count | % of FNs |")
    L.append("|---|---|---|")
    for cat in ["mislocalized", "low_confidence", "class_confusion", "completely_missed"]:
        n = stats["fn_cats"].get(cat, 0)
        pct = 100.0 * n / stats["fn"] if stats["fn"] else 0.0
        L.append(f"| {cat} | {n} | {pct:.1f}% |")
    L.append("")

    L.append("## FP Categories\n")
    L.append("| Category | Count | % of FPs |")
    L.append("|---|---|---|")
    for cat in ["background_fp", "class_confusion_fp", "localization_error", "duplicate"]:
        n = stats["fp_cats"].get(cat, 0)
        pct = 100.0 * n / stats["fp"] if stats["fp"] else 0.0
        L.append(f"| {cat} | {n} | {pct:.1f}% |")
    L.append("")

    L.append("## Size Distribution (bbox area, % of image)\n")
    L.append("| Set | Mean | Median | Min | Max |")
    L.append("|---|---|---|---|---|")
    for label, key in [("TP", "tp_areas"), ("FN", "fn_areas"), ("FP", "fp_areas")]:
        s = stats[key]
        if s:
            L.append(f"| {label} | {s[0]:.3f} | {s[1]:.3f} | {s[2]:.3f} | {s[3]:.3f} |")
        else:
            L.append(f"| {label} | N/A | N/A | N/A | N/A |")
    L.append("")

    L.append("## Confidence\n")
    L.append("| Set | Mean conf |")
    L.append("|---|---|")
    for label, key in [("TP", "tp_conf"), ("FP", "fp_conf"),
                       ("Low-conf FN", "lowconf_fn_conf"), ("Background FP", "bg_fp_conf")]:
        v = stats[key]
        L.append(f"| {label} | {v:.4f} |" if v is not None else f"| {label} | N/A |")
    L.append("")

    L.append("## Cross-Class Confusion Matrix (IoU=0.5)\n")
    L.append("| Class | TP | FP | FN |")
    L.append("|---|---|---|---|")
    for c in sorted(CLASS_NAMES):
        s = stats["cross"][c]
        L.append(f"| {CLASS_NAMES[c]} | {s['tp']} | {s['fp']} | {s['fn']} |")
    L.append("")
    confused_as = ", ".join(
        f"{CLASS_NAMES[c]} ({n})" for c, n in sorted(stats["fn_confused_as"].items(), key=lambda x: -x[1]))
    fp_over = ", ".join(
        f"{CLASS_NAMES[c]} ({n})" for c, n in sorted(stats["fp_over"].items(), key=lambda x: -x[1]))
    L.append(f"- Corrosion GTs predicted as: {confused_as or 'none'}")
    L.append(f"- Corrosion FPs overlapping GTs of: {fp_over or 'none'}\n")

    L.append("## Diagnosis\n")
    fn_n, fp_n = stats["fn"], stats["fp"]
    fn_cats, fp_cats = stats["fn_cats"], stats["fp_cats"]
    diag = []
    if fn_n and fn_cats.get("completely_missed", 0) / fn_n > 0.40:
        diag.append(f"Model lacks feature sensitivity for corrosion texture "
                    f"({100.0 * fn_cats['completely_missed'] / fn_n:.0f}% of FNs completely missed). "
                    f"Consider: SAHI slice training, P2 head, or more corrosion-specific augmentation.")
    if fn_n and fn_cats.get("low_confidence", 0) / fn_n > 0.30:
        diag.append(f"Model detects corrosion but lacks confidence "
                    f"({100.0 * fn_cats['low_confidence'] / fn_n:.0f}% of FNs low-confidence). "
                    f"Consider: lowering inference threshold, adding objectness branch, or calibration.")
    if fp_n and fp_cats.get("background_fp", 0) / fp_n > 0.30:
        diag.append(f"Corrosion texture confused with paint/shadow/reflection "
                    f"({100.0 * fp_cats['background_fp'] / fp_n:.0f}% of FPs are background FPs). "
                    f"Consider: hard-negative mining targeting those specific textures.")
    if fn_n and stats["scratch_confusion_fn"] / fn_n > 0.20:
        diag.append(f"Boundary ambiguity between corrosion and scratch "
                    f"({100.0 * stats['scratch_confusion_fn'] / fn_n:.0f}% of FNs are class confusion with scratch). "
                    f"Consider: clarifying annotation spec or merging classes.")
    fn_med = stats["fn_areas"][1] if stats["fn_areas"] else None
    if fn_med is not None and fn_med < 0.5:
        diag.append(f"Resolution problem: small corrosion patches lost in downsampling "
                    f"(median FN area {fn_med:.2f}%). Consider: SAHI or P2 head.")
    if fn_med is not None and fn_med > 5.0:
        diag.append(f"Annotation inconsistency on large patches "
                    f"(median FN area {fn_med:.2f}%). Consider: auditing annotations.")
    if not diag:
        diag.append("No critical failure mode dominates. Model performance is acceptable.")
    for d in diag:
        L.append(f"- {d}")
    L.append("")

    L.append("## Saved Example Files\n")
    for f in saved_files:
        L.append(f"- `{f}`")
    L.append("")

    (out_dir / "summary.md").write_text("\n".join(L))


def write_csvs(out_dir, fn_records, fp_records, model_path, test_count, stats):
    with open(out_dir / "fn_records.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "category", "gt_area_pct",
                                               "gt_aspect_ratio", "best_iou", "best_conf",
                                               "overlapping_class"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(fn_records)

    with open(out_dir / "fp_records.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "category", "pred_conf",
                                               "pred_area_pct", "overlapping_gt_class",
                                               "iou_with_gt"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(fp_records)

    rows = [
        ("model_path", model_path),
        ("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("test_images", test_count),
        ("precision", f"{stats['precision']:.4f}"),
        ("recall", f"{stats['recall']:.4f}"),
        ("f1", f"{stats['f1']:.4f}"),
        ("map50", f"{stats['map50']:.4f}"),
        ("tp", stats["tp"]), ("fn", stats["fn"]), ("fp", stats["fp"]),
    ]
    for cat, n in sorted(stats["fn_cats"].items()):
        rows.append((f"fn_{cat}", n))
    for cat, n in sorted(stats["fp_cats"].items()):
        rows.append((f"fp_{cat}", n))
    for key in ("tp_conf", "fp_conf", "lowconf_fn_conf", "bg_fp_conf"):
        v = stats[key]
        rows.append((key, f"{v:.4f}" if v is not None else ""))
    for key in ("tp_areas", "fn_areas", "fp_areas"):
        s = stats[key]
        for i, name in enumerate(("mean", "median", "min", "max")):
            rows.append((f"{key[:-5]}_area_{name}_pct", f"{s[i]:.4f}" if s else ""))
    with open(out_dir / "summary_stats.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerows(rows)


def main():
    print("=" * 80)
    print("CORROSION ERROR ANALYSIS")
    print("=" * 80)

    model_path = resolve_model_path()
    print(f"[*] Model: {model_path}")
    model = YOLO(model_path)

    image_paths = list_images(IMAGES_DIR)
    if not image_paths:
        sys.exit(f"ERROR: no images found in {IMAGES_DIR}")
    print(f"[*] Test images: {len(image_paths)}")
    image_paths_by_name = {p.name: p for p in image_paths}

    gts_by_image = load_ground_truths(LABELS_DIR, image_paths)
    print(f"[*] Images with annotations: {sum(1 for v in gts_by_image.values() if v)}")

    print("[*] Running inference (pass 1, boxes only)...")
    preds_by_image = run_inference(model, image_paths, keep_masks=False)

    all_fn, all_fp = [], []
    cross = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CLASS_NAMES}
    map50_per_image = []

    for img_path in image_paths:
        name = img_path.name
        gts = gts_by_image[name]
        preds = preds_by_image[name]
        try:
            with Image.open(img_path) as im:
                img_w, img_h = im.size
        except Exception as e:
            print(f"  [!] Skipping unreadable image {name}: {e}")
            continue
        fn, fp = categorize_corrosion_errors(name, gts, preds, img_w, img_h)
        all_fn.extend(fn)
        all_fp.extend(fp)
        cs = cross_class_stats(gts, preds, img_w, img_h)
        for c in cross:
            for k in ("tp", "fp", "fn"):
                cross[c][k] += cs[c][k]
        corr_gts_px = [(gt["bbox"][0] * img_w, gt["bbox"][1] * img_h,
                        gt["bbox"][2] * img_w, gt["bbox"][3] * img_h)
                       for gt in gts if gt["class_id"] == CORROSION]
        map50_per_image.append((corr_gts_px, [p for p in preds if p["class_id"] == CORROSION]))

    map50 = compute_map50(map50_per_image)
    print(f"[*] Corrosion: TP={sum(1 for r in all_fn if r['category'] == 'tp')} "
          f"FN={sum(1 for r in all_fn if r['category'] != 'tp')} FP={len(all_fp)} mAP50={map50:.4f}")

    # Pass 2: re-run inference with masks only for images that need FP visualizations
    fps_sorted = sorted(all_fp, key=lambda r: -r["pred_conf"])
    bg_sorted = sorted((r for r in all_fp if r["category"] == "background_fp"), key=lambda r: -r["pred_conf"])
    need_mask = {r["image_name"] for r in fps_sorted[:30]} | {r["image_name"] for r in bg_sorted[:15]}
    if need_mask:
        print(f"[*] Running inference (pass 2, masks) on {len(need_mask)} example images...")
        fresh = run_inference(model, [image_paths_by_name[n] for n in sorted(need_mask)], keep_masks=True)
        preds_by_image.update(fresh)
        for rec in all_fp:  # re-link _pred refs to the masked pred objects
            if rec["image_name"] not in fresh:
                continue
            old = rec["_pred"]
            for p in fresh[rec["image_name"]]:
                if p["class_id"] == old["class_id"] and p["bbox"] == old["bbox"]:
                    rec["_pred"] = p
                    break

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[*] Saving visual examples...")
    saved_files = save_examples(image_paths_by_name, preds_by_image, all_fn, all_fp, out_dir)

    print("[*] Generating report...")
    stats = build_stats(all_fn, all_fp, map50, cross)
    generate_report(model_path, len(image_paths), stats, saved_files, out_dir)
    write_csvs(out_dir, all_fn, all_fp, model_path, len(image_paths), stats)

    print(f"\nCORROSION ERROR ANALYSIS COMPLETE — check {OUTPUT_DIR}/summary.md")


if __name__ == "__main__":
    main()
