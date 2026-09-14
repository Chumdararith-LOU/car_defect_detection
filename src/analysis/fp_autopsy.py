#!/usr/bin/env python3
"""
Corrosion FP Autopsy at conf=0.05

Run on server:
  conda activate car_defect
  python src/analysis/fp_autopsy.py

Outputs:
  reports/fp_autopsy/report.html
  reports/fp_autopsy/crops/fp_*.jpg      (top-150 FP crops, 20% padding)
  reports/fp_autopsy/crops/context_*.jpg (full-image thumbnails with FP mask overlay)
"""

import html
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
for _p in (_PROJECT_ROOT, _VENDOR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ultralytics import YOLO

CORROSION = 1
MODEL_PATHS = [
    "runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt",
    "runs/segment/runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt",
]
TEST_DIR = "data/processed/yolo_seg/images/test"
TEST_LABELS_DIR = "data/processed/yolo_seg/labels/test"
OUTPUT_DIR = "reports/fp_autopsy"
CONF, NMS_IOU, IMGSZ = 0.05, 0.5, 1024
TP_IOU = 0.5
TOP_N = 150
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


def load_gt_corrosion_boxes(labels_dir, image_paths):
    """image_name -> list of normalized (x1, y1, x2, y2) corrosion GT boxes.

    Handles both label formats: segmentation (polygon vertices) and
    detection (cx cy w h -> converted to xyxy).
    """
    boxes_by_image = {}
    for img_path in image_paths:
        label_path = Path(labels_dir) / (img_path.stem + ".txt")
        boxes = []
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 5 or int(parts[0]) != CORROSION:
                        continue
                    if len(parts) == 5:  # detection format: cx cy w h
                        cx, cy, w, h = (float(x) for x in parts[1:5])
                        boxes.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
                    else:  # segmentation format: polygon vertices
                        coords = [float(x) for x in parts[1:]]
                        if len(coords) % 2:
                            continue
                        xs, ys = coords[0::2], coords[1::2]
                        boxes.append((min(xs), min(ys), max(xs), max(ys)))
        boxes_by_image[img_path.name] = boxes
    return boxes_by_image


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


def run_pass1(model, image_paths):
    """name -> {"size": (w, h), "preds": [{conf, bbox(px)}]} for corrosion only."""
    out = {}
    for i, p in enumerate(image_paths):
        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{len(image_paths)}] {p.name}")
        res = model.predict(str(p), conf=CONF, iou=NMS_IOU, imgsz=IMGSZ, verbose=False)[0]
        w, h = res.orig_shape[1], res.orig_shape[0]
        preds = []
        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy().astype(int)
            for j in range(len(xyxy)):
                if int(cls[j]) == CORROSION:
                    preds.append({"conf": float(confs[j]), "bbox": xyxy[j].tolist()})
        out[p.name] = {"size": (w, h), "preds": preds}
    return out


def run_pass2(model, image_paths):
    """name -> list of ALL preds with masks (for attaching masks to chosen FPs)."""
    out = {}
    for i, p in enumerate(image_paths):
        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{len(image_paths)}] {p.name}")
        res = model.predict(str(p), conf=CONF, iou=NMS_IOU, imgsz=IMGSZ, verbose=False)[0]
        preds = []
        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy().astype(int)
            masks = res.masks.data.cpu().numpy().astype(bool) if res.masks is not None else None
            for j in range(len(xyxy)):
                pred = {"conf": float(confs[j]), "class_id": int(cls[j]),
                        "bbox": xyxy[j].tolist()}
                if masks is not None:
                    m = masks[j]
                    if m.shape[:2] != res.orig_shape:  # vendor ultralytics may return inference-res masks
                        m = cv2.resize(m.astype(np.uint8), (res.orig_shape[1], res.orig_shape[0]),
                                       interpolation=cv2.INTER_NEAREST).astype(bool)
                    pred["mask"] = m
                preds.append(pred)
        out[p.name] = preds
    return out


def make_crop(img, bbox, out_path):
    w, h = img.size
    x1, y1, x2, y2 = bbox
    pw, ph = 0.2 * (x2 - x1), 0.2 * (y2 - y1)
    box = (max(0, int(x1 - pw)), max(0, int(y1 - ph)),
           min(w, int(x2 + pw)), min(h, int(y2 + ph)))
    img.crop(box).save(out_path, quality=90)


def make_context(img, mask, out_path, max_dim=512):
    arr = np.array(img)
    if mask is not None:
        m = np.asarray(mask) > 0.5
        if m.shape != arr.shape[:2]:
            m = cv2.resize(m.astype(np.uint8), (arr.shape[1], arr.shape[0]),
                           interpolation=cv2.INTER_NEAREST).astype(bool)
        arr[m] = arr[m] * 0.5 + np.array([255, 0, 0], dtype=float) * 0.5
    thumb = Image.fromarray(arr)
    scale = max_dim / max(thumb.size)
    if scale < 1:
        thumb = thumb.resize((int(thumb.size[0] * scale), int(thumb.size[1] * scale)),
                             Image.Resampling.BILINEAR)
    thumb.save(out_path, quality=85)


def build_html(top, total_fps, out_path):
    L = []
    L.append("<!DOCTYPE html>")
    L.append('<html><head><meta charset="utf-8">')
    L.append("<title>Corrosion FP Autopsy</title>")
    L.append("<style>")
    L.append("body { background:#111; color:#eee; font-family:monospace; margin:20px; }")
    L.append("h1 { font-size:18px; }")
    L.append(".summary { color:#aaa; font-size:13px; margin-bottom:16px; }")
    L.append(".grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(360px, 1fr)); gap:16px; }")
    L.append(".card { background:#1c1c1c; border:1px solid #333; border-radius:6px; padding:10px; }")
    L.append(".card img.crop { width:100%; border-radius:4px; display:block; }")
    L.append(".card img.ctx { width:100%; border-radius:4px; display:block; margin-top:8px; opacity:0.85; }")
    L.append(".meta { font-size:12px; color:#aaa; margin-top:6px; word-break:break-all; }")
    L.append(".conf { color:#ff5555; font-weight:bold; }")
    L.append("</style></head><body>")
    L.append("<h1>Corrosion FP Autopsy (Threshold 0.05). Are these missed annotations or background noise?</h1>")
    L.append(f'<p class="summary">Total corrosion FPs at conf={CONF}: {total_fps} | '
             f"Showing top {len(top)} by confidence | crop = FP region +20% padding, "
             f"thumbnail = full image with FP mask overlay (red)</p>")
    L.append('<div class="grid">')
    for i, rec in enumerate(top, 1):
        L.append('<div class="card">')
        L.append(f'<img class="crop" src="crops/fp_{i:03d}_conf_{rec["conf"]:.3f}.jpg">')
        L.append(f'<img class="ctx" src="crops/context_{i:03d}.jpg">')
        L.append(f'<div class="meta"><span class="conf">{rec["conf"]:.3f}</span> '
                 f'&mdash; {html.escape(rec["image_name"])}</div>')
        L.append("</div>")
    L.append("</div></body></html>")
    out_path.write_text("\n".join(L))


def main():
    print("=" * 80)
    print("CORROSION FP AUTOPSY (conf=0.05)")
    print("=" * 80)

    model_path = resolve_model_path()
    print(f"[*] Model: {model_path}")
    model = YOLO(model_path)

    image_paths = list_images(TEST_DIR)
    print(f"[*] Test images: {len(image_paths)}")
    gt_boxes = load_gt_corrosion_boxes(TEST_LABELS_DIR, image_paths)

    print(f"[*] Pass 1: inference conf={CONF} iou={NMS_IOU} imgsz={IMGSZ} (boxes only)...")
    pass1 = run_pass1(model, image_paths)

    fps = []
    for name, entry in pass1.items():
        w, h = entry["size"]
        gt_px = [(b[0] * w, b[1] * h, b[2] * w, b[3] * h) for b in gt_boxes[name]]
        for pred in entry["preds"]:
            best = max((compute_iou(pred["bbox"], gb) for gb in gt_px), default=0.0)
            if best < TP_IOU:
                fps.append({"conf": pred["conf"], "bbox": pred["bbox"], "image_name": name})
    fps.sort(key=lambda r: -r["conf"])
    top = fps[:TOP_N]
    print(f"[*] Total corrosion FPs at conf={CONF}: {len(fps)} | keeping top {len(top)}")

    crops_dir = Path(OUTPUT_DIR) / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)

    print("[*] Pass 2: inference with masks on FP example images...")
    unique_images = sorted({r["image_name"] for r in top})
    pass2 = run_pass2(model, [p for p in image_paths if p.name in set(unique_images)])

    print("[*] Saving crops and context thumbnails...")
    for i, rec in enumerate(top, 1):
        name = rec["image_name"]
        img = Image.open(Path(TEST_DIR) / name).convert("RGB")
        make_crop(img, rec["bbox"], crops_dir / f"fp_{i:03d}_conf_{rec['conf']:.3f}.jpg")
        mask = None
        for p in pass2.get(name, []):
            if p.get("class_id") == CORROSION and p["bbox"] == rec["bbox"]:
                mask = p.get("mask")
                break
        make_context(img, mask, crops_dir / f"context_{i:03d}.jpg")
        img.close()

    print("[*] Writing HTML report...")
    mean_conf = float(np.mean([r["conf"] for r in top])) if top else 0.0
    build_html(top, len(fps), Path(OUTPUT_DIR) / "report.html")

    print(f"Total Corrosion FPs found at 0.05 threshold: {len(fps)}")
    print(f"Mean confidence of the top {len(top)} FPs: {mean_conf:.4f}")
    print("FP AUTOPSY COMPLETE — pull reports/fp_autopsy/report.html to your local machine and review.")


if __name__ == "__main__":
    main()
