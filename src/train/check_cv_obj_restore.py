#!/usr/bin/env python3
"""Acceptance check: restore_cv_obj recovers trained cv_obj from a checkpoint.

Run from the repo root:
    python src/train/check_cv_obj_restore.py [path/to/best.pt]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import torch

# Importing src.train.train registers Segment26WithObjectness in
# ultralytics.nn.modules.head (required to unpickle the checkpoint) and
# puts the repo root + vendor on sys.path.
from src.train.train import restore_cv_obj
from src.models.segment_head_with_obj import Segment26WithObjectness

PRESET = sys.argv[1] if len(sys.argv) > 1 else "runs/segment/seesaw_surgical_objectness-26/weights/best.pt"

ckpt = torch.load(PRESET, map_location="cpu", weights_only=False)
module = (ckpt.get("ema") or ckpt.get("model")) if isinstance(ckpt, dict) else ckpt
sd = module.state_dict()
pat = re.compile(r"model\.\d+\.cv_obj\.(\d+)\.weight")
keys = [k for k in sd if pat.match(k)]
ch = tuple(sd[k].shape[1] for k in sorted(keys, key=lambda k: int(pat.match(k).group(1))))
print(f"checkpoint cv_obj input channels: {ch}")

head = Segment26WithObjectness(nc=7, nm=32, npr=256, reg_max=16, ch=ch)
n = restore_cv_obj(head, PRESET)
assert n > 0, "no cv_obj tensors restored"
for i, m in enumerate(head.cv_obj):
    w = m.weight.abs().max().item()
    b = m.bias.item()
    print(f"level {i}: weight_absmax={w:.6f} bias={b:.4f}")
    assert w > 0.0 and b != -2.0, f"level {i} still at init values"
print("PASS: cv_obj restored with trained (non-init) values")
