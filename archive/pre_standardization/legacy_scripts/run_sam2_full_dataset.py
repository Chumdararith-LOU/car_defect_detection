import json
from pathlib import Path
import cv2
import numpy as np
import torch
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from tqdm import tqdm

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
ANNOTATIONS_PATH = (
    PROJECT_ROOT / "data" / "cvat_staging" / "unified_cvat_annotations.json"
)
IMAGES_DIR = PROJECT_ROOT / "data" / "cvat_staging" / "images"
OUTPUT_JSON = (
    PROJECT_ROOT / "data" / "cvat_staging" / "unified_cvat_annotations_sam2.json"
)
CHECKPOINT_PATH = "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/cvat/checkpoints/sam2_hiera_large.pt"

# Device
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"[*] Loading SAM 2 Large on {device}...")
predictor = SAM2ImagePredictor(
    build_sam2("sam2_hiera_l.yaml", str(CHECKPOINT_PATH), device=device)
)

with open(ANNOTATIONS_PATH, "r") as f:
    coco = json.load(f)

img_lookup = {img["id"]: img["file_name"] for img in coco["images"]}

# Group annotations by image for fast inference
img_to_anns = {}
for ann in coco["annotations"]:
    img_to_anns.setdefault(ann["image_id"], []).append(ann)

print(
    f"[*] Processing {len(coco['annotations'])} annotations across {len(img_to_anns)} images..."
)

for img_id, anns in tqdm(img_to_anns.items(), desc="SAM 2 Refinement"):
    img_name = img_lookup.get(img_id)
    if not img_name:
        continue

    img_path = IMAGES_DIR / img_name
    if not img_path.exists():
        continue

    image = Image.open(img_path).convert("RGB")
    img_np = np.array(image)
    h_img, w_img, _ = img_np.shape
    predictor.set_image(img_np)

    for ann in anns:
        x, y, w, h = ann["bbox"]
        if w <= 0 or h <= 0:
            continue

        x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
        box = np.array([x1, y1, x2, y2])
        center_point = np.array([[int(x + w / 2), int(y + h / 2)]])

        try:
            masks, scores, _ = predictor.predict(
                point_coords=center_point,
                point_labels=np.array([1]),
                box=box,
                multimask_output=True,
            )

            masks_bool = [
                (
                    m.detach().cpu().numpy().astype(bool)
                    if isinstance(m, torch.Tensor)
                    else np.asarray(m, dtype=bool)
                )
                for m in masks
            ]

            bbox_area = w * h
            best_mask = None
            best_score = -1

            for mask, score in zip(masks_bool, scores):
                if np.sum(mask) > (bbox_area * 2.5):
                    continue
                if score > best_score:
                    best_score = score
                    best_mask = mask

            if best_mask is None:
                best_mask = masks_bool[0]

            # Clip mask to box + buffer
            buf = 10
            clip_mask = np.zeros((h_img, w_img), dtype=bool)
            clip_mask[
                max(0, y1 - buf) : min(h_img, y2 + buf),
                max(0, x1 - buf) : min(w_img, x2 + buf),
            ] = True

            constrained_mask = np.logical_and(best_mask, clip_mask).astype(np.uint8)

            # Convert binary mask to COCO polygon
            contours, _ = cv2.findContours(
                constrained_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            segmentation = []
            for contour in contours:
                if len(contour) >= 3:
                    segmentation.append(contour.flatten().tolist())

            if segmentation:
                ann["segmentation"] = segmentation

        except Exception:
            continue

# Save updated JSON
with open(OUTPUT_JSON, "w") as f:
    json.dump(coco, f, indent=2)

print(f"\n[✔] SAM 2 pass complete! Saved to '{OUTPUT_JSON}'")
