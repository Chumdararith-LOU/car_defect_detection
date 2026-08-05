"""SAHI production inference for 7-class car defect segmentation (YOLO26m-seg).

Pipeline (validated in phase3_diagnostics.ipynb, Phase 3):
  1. Slice image into native-res 640x640 patches (15% overlap).
  2. Per-patch inference (SAHI, ultralytics backend).
  3. Per-class acceptance rules (confidence + min mask area).
  4. Greedy per-class mask-IOS NMS (Intersection over Smaller mask area).

Operator-tunable: presets / per-class conf live in the YAML (or any dict
passed at runtime). The industrial UI may override them per shift.
"""

import cv2
import numpy as np
import yaml
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_lamp",
    5: "corrosion",
    6: "disjoint_part",
}


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def mask_ios(a_mask, a_area, b_mask, b_area):
    inter = int(np.logical_and(a_mask, b_mask).sum())
    smaller = min(a_area, b_area)
    return inter / smaller if smaller > 0 else 0.0


def _boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class SahiInference:
    def __init__(self, model_path, cfg, device="cuda:0"):
        self.cfg = cfg
        self.rules = cfg["presets"][cfg["preset"]]["class_rules"]
        self.model_conf = min(float(r["conf"]) for r in self.rules.values())
        self.model = AutoDetectionModel.from_pretrained(
            model_path=model_path,
            model_type=cfg.get("model_type", "yolov8"),
            device=device,
            confidence_threshold=self.model_conf,
        )

    def _accepted(self, cls_id, score, area):
        r = self.rules.get(
            str(cls_id), self.rules.get("default", {"conf": 0.25, "min_area": 0})
        )
        return score >= float(r["conf"]) and area >= int(r["min_area"])

    def predict(self, image_path):
        s = self.cfg["sahi"]
        result = get_sliced_prediction(
            image_path,
            self.model,
            slice_height=int(s["slice_size"]),
            slice_width=int(s["slice_size"]),
            overlap_height_ratio=float(s["overlap_ratio"]),
            overlap_width_ratio=float(s["overlap_ratio"]),
        )
        dets = []
        for p in result.object_prediction_list:
            try:
                cls_id = int(p.category.id)
            except Exception:
                continue
            m = np.asarray(p.mask.bool_mask) > 0.5
            area = int(m.sum())
            if not self._accepted(cls_id, p.score.value, area):
                continue
            ys, xs = np.nonzero(m)
            dets.append(
                {
                    "cls": cls_id,
                    "name": CLASS_NAMES.get(cls_id, str(p.category.name)),
                    "score": float(p.score.value),
                    "mask": m,
                    "area": area,
                    "bbox": [
                        int(xs.min()),
                        int(ys.min()),
                        int(xs.max()),
                        int(ys.max()),
                    ],
                }
            )

        thr = float(self.cfg["nms"]["ios_threshold"])
        dets.sort(key=lambda d: -d["score"])
        kept = []
        for d in dets:
            if not any(
                d["cls"] == k["cls"]
                and _boxes_overlap(d["bbox"], k["bbox"])
                and mask_ios(d["mask"], d["area"], k["mask"], k["area"]) >= thr
                for k in kept
            ):
                kept.append(d)
        return kept

    def visualize(self, image_path, preds, gt_label_path=None):
        img = cv2.imread(image_path)
        vis = img.copy()
        if gt_label_path:
            H0, W0 = img.shape[:2]
            with open(gt_label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 7 and int(parts[0]) in (5, 6):
                        coords = list(map(float, parts[1:]))
                        pts = np.array(
                            [
                                [int(coords[i] * W0), int(coords[i + 1] * H0)]
                                for i in range(0, len(coords) - 1, 2)
                            ],
                            np.int32,
                        )
                        cv2.polylines(vis, [pts], True, (0, 255, 0), 2)
        for d in preds:
            cnts, _ = cv2.findContours(
                d["mask"].astype(np.uint8) * 255,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if d["cls"] in (5, 6):
                cv2.drawContours(vis, cnts, -1, (0, 0, 255), 2)
                cv2.putText(
                    vis,
                    f"{d['name']} {d['score']:.2f}",
                    (d["bbox"][0], max(12, d["bbox"][1] - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                )
            else:
                cv2.drawContours(vis, cnts, -1, (255, 0, 0), 1)
        return vis


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", default="overlay.jpg")
    ap.add_argument("--device", default="cuda:0")
    a = ap.parse_args()
    engine = SahiInference(a.model, load_config(a.config), device=a.device)
    preds = engine.predict(a.image)
    cv2.imwrite(a.out, engine.visualize(a.image, preds))
    print(f"{len(preds)} predictions saved to {a.out}")
    for d in preds:
        print(f"  {d['name']} {d['score']:.3f} bbox={d['bbox']}")
