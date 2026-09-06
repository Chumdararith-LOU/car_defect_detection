"""
Stage 2 — Full fine-tune, all layers unfrozen, with differential learning rates
(backbone/neck slower than head) and a close_mosaic schedule so the final
epochs train on un-mosaicked, context-preserved images — matching the real
eval/deployment distribution.

Resumes from Stage 1's best checkpoint. Written against standard Ultralytics
YOLO conventions; confirm class/method names match your specific build.
"""

import torch
from ultralytics.models.yolo.segment import SegmentationTrainer

BACKBONE_NECK_LR_MULT = 0.1  # backbone/neck learns 10x slower than the head
SPLIT_LAYER_IDX = 15  # same index used for `freeze: 15` elsewhere in this
# project — everything below model.model[15] is
# treated as "backbone/neck", everything at/above
# as "head". VERIFY this matches your architecture's
# actual neck/head boundary before running.


class DifferentialLRTrainer(SegmentationTrainer):
    def build_optimizer(
        self, model, name="auto", lr=0.001, momentum=0.9, decay=1e-5, iterations=1e5
    ):
        backbone_params, head_params = [], []
        for n, p in model.named_parameters():
            if not p.requires_grad:
                continue
            try:
                idx = int(n.split(".")[1])  # param names look like "model.<idx>.<...>"
            except (IndexError, ValueError):
                idx = 999  # unparseable -> treat as head (safer default)
            (backbone_params if idx < SPLIT_LAYER_IDX else head_params).append(p)

        optimizer = torch.optim.SGD(
            [
                {"params": backbone_params, "lr": lr * BACKBONE_NECK_LR_MULT},
                {"params": head_params, "lr": lr},
            ],
            momentum=momentum,
            nesterov=True,
        )
        print(
            f"Optimizer groups -> backbone: {len(backbone_params)} params "
            f"@ lr={lr * BACKBONE_NECK_LR_MULT:.5f} | head: {len(head_params)} "
            f"params @ lr={lr:.5f}"
        )
        return optimizer


overrides = dict(
    model="model5_resume_adapt/stage1_head_warmup/weights/best.pt",  # Stage 1's BEST, not last
    data="cvat_clean_2200.yaml",
    imgsz=1024,
    epochs=120,
    freeze=0,  # everything trainable; the LR differential replaces the hard freeze
    mosaic=1.0,
    scale=0.5,
    degrees=30.0,
    erasing=0.4,
    multi_scale=True,
    close_mosaic=25,  # last 25 epochs: mosaic OFF, head trains/is judged on real panel context
    patience=20,
    lr0=0.001,  # this is the HEAD lr; backbone gets 0.1x via build_optimizer above
    project="model5_resume_adapt",
    name="stage2_differential_finetune",
    val=True,
)

trainer = DifferentialLRTrainer(overrides=overrides)
trainer.train()
