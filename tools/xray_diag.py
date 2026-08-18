#!/usr/bin/env python3
"""
G3: Raw-logits X-Ray diagnostic (Phase 3 notebook, Cells 6-8), ported for Mac.

Bypasses the prediction API (Commandment #2): intercepts the head's raw
sigmoid probabilities at the ground-truth location, so you can see signal
that thresholding/NMS would silently discard.

Usage:
  python tools/xray_diag.py --model runs/segment/.../best.pt [--limit 7]
"""

import argparse
import glob
import os
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO

TARGET_CLASSES = {5: "corrosion", 6: "disjoint_part"}
CONTROL_CLASS = 3  # glass_shatter: common + well-learned (Commandment #4 control)
CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_lamp",
    5: "corrosion",
    6: "disjoint_part",
}


def letterbox(img, new_shape=1024):
    h, w = img.shape[:2]
    scale = min(new_shape / w, new_shape / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    dw, dh = (new_shape - nw) / 2, (new_shape - nh) / 2
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
    )
    return padded, scale, dw, dh


def to_tensor(img_bgr, device):
    rgb = img_bgr[:, :, ::-1].copy()
    t = torch.from_numpy(rgb).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    return t.to(device)


def extract_patch(img, cx, cy, size=1024):
    """Native-resolution crop centered on the target (SAHI patch simulation)."""
    H0, W0 = img.shape[:2]
    if H0 < size or W0 < size:
        img = cv2.copyMakeBorder(
            img,
            0,
            max(0, size - H0),
            0,
            max(0, size - W0),
            cv2.BORDER_CONSTANT,
            value=(114, 114, 114),
        )
        H0, W0 = img.shape[:2]
    x1 = min(max(int(round(cx - size / 2)), 0), W0 - size)
    y1 = min(max(int(round(cy - size / 2)), 0), H0 - size)
    return img[y1 : y1 + size, x1 : x1 + size], x1, y1


def classify_signal(best_p):
    if best_p < 0.05:
        return "ABSENT -> SAHI/tiling required (focal loss cannot help)"
    if best_p < 0.40:
        return "WEAK -> focal loss retraining / threshold calibration"
    return "PRESENT -> post-processing/threshold issue"


class XRay:
    def __init__(self, model_path, device):
        self.device = device
        model = YOLO(model_path)
        self.net = model.model
        self.net.eval()
        self.net.to(device)
        self.head = self.net.model[-1]

        # Classification branch (Commandment #3: BCE/focal loss -> sigmoid)
        if hasattr(self.head, "one2one_cv3"):
            self.cls_branch, branch = self.head.one2one_cv3, "one2one_cv3"
        elif hasattr(self.head, "cv3"):
            self.cls_branch, branch = self.head.cv3, "cv3"
        else:
            raise RuntimeError(
                f"Head {type(self.head).__name__} has no cv3/one2one_cv3"
            )

        # Feature indices feeding the head (P3/P4/P5)
        f = getattr(self.head, "f", None)
        derived = (
            [i for i in f if isinstance(i, int) and i >= 0]
            if isinstance(f, (list, tuple))
            else []
        )
        self.feat_idx = (
            derived if len(derived) == len(self.cls_branch) else [16, 19, 22]
        )
        self.head_i = self.head.i

        print(
            f"Head: {type(self.head).__name__} | branch: {branch} | "
            f"feats: {self.feat_idx} | nc: {getattr(self.head, 'nc', '?')}"
        )

        # Smoke test; fall back from MPS to CPU if any op is unsupported
        try:
            with torch.no_grad():
                self.get_feats(torch.zeros(1, 3, 640, 640, device=self.device))
        except Exception as e:
            if self.device.type == "mps":
                print(f"MPS forward failed ({e}) -> falling back to CPU")
                self.device = torch.device("cpu")
                self.net.to("cpu")
            else:
                raise

    @torch.no_grad()
    def get_feats(self, t):
        """Replicates ultralytics _predict_once wiring up to the head."""
        feats, y, x = {}, [], t
        for m in self.net.model:
            if m.i == self.head_i:
                break
            x = m(x) if m.f == -1 else m([x if j == -1 else y[j] for j in m.f])
            y.append(x if m.i in self.net.save else None)
            if m.i in self.feat_idx:
                feats[m.i] = x
        return feats

    @torch.no_grad()
    def xray_img(self, img_bgr, bbox_abs, cls_id, neigh=2):
        padded, scale, dw, dh = letterbox(img_bgr)
        feats = self.get_feats(to_tensor(padded, self.device))
        x1, y1, x2, y2 = bbox_abs
        cx = ((x1 + x2) / 2) * scale + dw
        cy = ((y1 + y2) / 2) * scale + dh
        rows = []
        for k, fi in enumerate(self.feat_idx):
            pmap = torch.sigmoid(self.cls_branch[k](feats[fi]))[0]  # [nc, H, W]
            _, H, W = pmap.shape
            stride = int(round(padded.shape[0] / H))
            gx = min(max(int(cx / stride), 0), W - 1)
            gy = min(max(int(cy / stride), 0), H - 1)
            region = pmap[
                :,
                max(0, gy - neigh) : gy + neigh + 1,
                max(0, gx - neigh) : gx + neigh + 1,
            ]
            per_cls_max = region.flatten(1).max(dim=1).values
            rows.append(
                {
                    "k": k,
                    "stride": stride,
                    "grid": (gx, gy),
                    "target_p": per_cls_max[cls_id].item(),
                    "argmax_cls": per_cls_max.argmax().item(),
                    "argmax_p": per_cls_max.max().item(),
                }
            )
        return rows

    def xray(self, img_path, bbox_abs, cls_id):
        return self.xray_img(cv2.imread(str(img_path)), bbox_abs, cls_id)


def collect_instances(labels_dir, images_dir, class_ids):
    instances = []
    for label_file in sorted(glob.glob(str(Path(labels_dir) / "*.txt"))):
        base = os.path.basename(label_file)[:-4]
        img_path = None
        for ext in (".jpg", ".jpeg", ".png", ".JPG", ".PNG"):
            p = Path(images_dir) / (base + ext)
            if p.exists():
                img_path = p
                break
        if not img_path:
            continue
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        img_h, img_w = img.shape[:2]
        with open(label_file) as f:
            for line in f:
                parts = line.strip().split()
                try:
                    if len(parts) >= 5 and int(parts[0]) in class_ids:
                        coords = list(map(float, parts[1:]))
                        xs, ys = coords[0::2], coords[1::2]
                        instances.append(
                            {
                                "image": base,
                                "path": img_path,
                                "cls": int(parts[0]),
                                "bbox": [
                                    int(min(xs) * img_w),
                                    int(min(ys) * img_h),
                                    int(max(xs) * img_w),
                                    int(max(ys) * img_h),
                                ],
                            }
                        )
                except (ValueError, IndexError):
                    continue
    return instances


def main():
    ap = argparse.ArgumentParser(description="Raw-logits X-Ray diagnostic (Phase 3)")
    ap.add_argument("--model", required=True, help="path to a stage2 .pt checkpoint")
    ap.add_argument("--val-root", default="data/processed/yolo_seg_clean_2200_7cls/val")
    ap.add_argument("--limit", type=int, default=7)
    args = ap.parse_args()

    val = Path(args.val_root)
    device = (
        torch.device("mps")
        if torch.backends.mps.is_available()
        else torch.device("cpu")
    )
    print(f"Device: {device}")
    xr = XRay(args.model, device)

    # ---------- 1. CONTROL (Commandment #4) ----------
    control = collect_instances(val / "labels", val / "images", {CONTROL_CLASS})
    if not control:
        print("\nWARNING: no glass_shatter instance found - skipping control check")
    else:
        c = control[0]
        rows = xr.xray(c["path"], c["bbox"], CONTROL_CLASS)
        best = max(r["target_p"] for r in rows)
        print(f"\nCONTROL: {c['image']} | glass_shatter | bbox {c['bbox']}")
        for r in rows:
            print(
                f"  scale {r['k']} (stride {r['stride']}, grid {r['grid']}): "
                f"target P={r['target_p']:.4f} | argmax cls={r['argmax_cls']} "
                f"{CLASS_NAMES.get(r['argmax_cls'], '?')} ({r['argmax_p']:.4f})"
            )
        verdict = (
            "PASS"
            if best >= 0.5
            else "SUSPECT - fix the diagnostic before trusting failure analysis"
        )
        print(f"CONTROL verdict: {verdict} (best target P={best:.4f})")

    # ---------- 2. X-Ray rare classes ----------
    rare = collect_instances(val / "labels", val / "images", set(TARGET_CLASSES))
    cases = rare[: args.limit]
    print(f"\nRare-class instances: {len(rare)} found, x-raying first {len(cases)}")
    letterbox_best = {}
    for i, case in enumerate(cases):
        rows = xr.xray(case["path"], case["bbox"], case["cls"])
        best_row = max(rows, key=lambda r: r["target_p"])
        letterbox_best[i] = best_row["target_p"]
        w = case["bbox"][2] - case["bbox"][0]
        h = case["bbox"][3] - case["bbox"][1]
        print(
            f"\n--- Case {i + 1}: {case['image']} | {TARGET_CLASSES[case['cls']]} | {w}x{h}px ---"
        )
        for r in rows:
            print(
                f"  scale {r['k']} (stride {r['stride']}, grid {r['grid']}): "
                f"target P={r['target_p']:.4f} | argmax cls={r['argmax_cls']} "
                f"{CLASS_NAMES.get(r['argmax_cls'], '?')} ({r['argmax_p']:.4f})"
            )
        print(f"  SIGNAL: {classify_signal(best_row['target_p'])}")

    # ---------- 3. SAHI patch simulation ----------
    print("\n" + "=" * 64)
    print("SAHI PATCH SIMULATION (native-res 640x640 crop vs letterbox)")
    print("=" * 64)
    for i, case in enumerate(cases):
        img = cv2.imread(str(case["path"]))
        x1, y1, x2, y2 = case["bbox"]
        patch, px, py = extract_patch(img, (x1 + x2) / 2, (y1 + y2) / 2)
        local_bbox = [x1 - px, y1 - py, x2 - px, y2 - py]
        rows = xr.xray_img(patch, local_bbox, case["cls"])
        best_row = max(rows, key=lambda r: r["target_p"])
        lb = letterbox_best[i]
        delta = best_row["target_p"] - lb
        print(
            f"Case {i + 1} {TARGET_CLASSES[case['cls']]:>13} | "
            f"letterbox P={lb:.4f} -> native-patch P={best_row['target_p']:.4f} "
            f"(delta {delta:+.4f}) | {classify_signal(best_row['target_p'])}"
        )


if __name__ == "__main__":
    main()
