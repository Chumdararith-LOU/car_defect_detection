"""
Stage 1 — Remap Model 1's 7-class head to 8 classes, then warm up the new head
with the backbone/neck frozen.

Run once, before Stage 2. Written against standard Ultralytics YOLO conventions;
confirm attribute/class names match your specific YOLO26m-seg build before running.
"""

import torch
from ultralytics import YOLO

MODEL1_CKPT = "runs/model1_professor_baseline/weights/epoch101.pt"  # Model 1's PEAK checkpoint, not the epoch-200 final
NEW_NC = 8
DATA_YAML = "cvat_clean_2200.yaml"  # CVAT clean 2,200-image split, 8 classes, val = clean 220-image test set

# --- Step 1: architecture surgery -------------------------------------------
# Build a fresh 8-class model from the same architecture, then load Model 1's
# weights with strict=False so every layer EXCEPT the head (shape-mismatched
# due to 7 -> 8 classes) transfers. The head gets a fresh random init.
model = YOLO("yolo26m-seg.yaml")  # architecture only, no weights
model.model.nc = NEW_NC  # set nc before load so the head is built at 8 classes

ckpt = torch.load(MODEL1_CKPT, map_location="cpu")
src_state = ckpt["model"].float().state_dict() if "model" in ckpt else ckpt

missing, unexpected = model.model.load_state_dict(src_state, strict=False)
print(f"Skipped / re-initialized layers (should be head-only): {missing}")
print(f"Unused source keys: {unexpected}")

torch.save({"model": model.model}, "model1_remapped_8class_init.pt")

# --- Step 2: head-only warmup, backbone/neck frozen -------------------------
model = YOLO("model1_remapped_8class_init.pt")

model.train(
    data=DATA_YAML,
    imgsz=1024,
    epochs=15,  # matches the existing freeze-cliff convention (unfreeze at 16)
    freeze=15,  # freeze backbone+neck; only the remapped head trains
    mosaic=1.0,
    scale=0.5,
    degrees=30.0,
    erasing=0.4,
    multi_scale=True,
    lr0=0.01,  # normal LR is fine — only a small head is training
    patience=0,  # fixed-length warmup, no early stop
    project="model5_resume_adapt",
    name="stage1_head_warmup",
    val=True,
)
