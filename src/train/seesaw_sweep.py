import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG_DIR = ROOT / "configs" / "train" / "stage2"
REPORT_PATH = ROOT / "reports" / "phase2_seesaw_sweep_plan.md"

P_GRID = [0.6, 0.8, 1.0]
Q_GRID = [1.5, 2.0, 2.5]

CFG_TEMPLATE = """task: segment
loss_type: seesaw
seesaw_p: {p}
seesaw_q: {q}
model_preset: model5_resume_adapt/model1_remapped_7class_init.pt

# train.py surgically unfreezes layers 0-4 + head under freeze: 23
surgical_mode: early_texture

project_name: car_defect_detection
run_name: {run_name}
multi_scale: false

# 20% stratified subset for fast hyperparameter screening
dataset_config: "data/processed/yolo_seg_subset/data.yaml"
epochs: 25
imgsz: 1024
batch_size: 8
patience: 15
device: 0
workers: 8
amp: true

freeze: 23
optimizer: AdamW
lr0: 0.001
lrf: 0.01

augmentations:
  hsv_h: 0.03
  hsv_s: 0.4
  hsv_v: 0.5
  degrees: 15.0
  scale: 0.2
  perspective: 0.0005
  fliplr: 0.5
  mosaic: 0.0
  mixup: 0.0
  erasing: 0.2
  close_mosaic: 10
"""


def tag(v: float) -> str:
    return str(v).replace(".", "")


def main():
    runs = []
    for p, q in itertools.product(P_GRID, Q_GRID):
        run_name = f"seesaw_sweep_p{tag(p)}_q{tag(q)}"
        cfg_path = CFG_DIR / f"{run_name}.yaml"
        cfg_path.write_text(CFG_TEMPLATE.format(p=p, q=q, run_name=run_name))
        runs.append((p, q, cfg_path))

    commands = [
        f"python src/train/train.py --config {cfg.relative_to(ROOT)}"
        for _, _, cfg in runs
    ]
    print("Seesaw sweep — 9 runs (25 epochs, yolo_seg_subset, early_texture):")
    for cmd in commands:
        print(f"  {cmd}")

    grid_rows = "\n".join(
        f"| {i} | {p} | {q} | configs/train/stage2/{cfg.name} |"
        for i, (p, q, cfg) in enumerate(runs, 1)
    )
    result_rows = "\n".join(f"| {p} | {q} |  |  |  |  |  |  |  |  |  |" for p, q, _ in runs)

    report = f"""# Phase 2: Seesaw Loss Hyperparameter Sweep Plan

## Rationale

The 7-class Stage 2 dataset has a ~31:1 instance imbalance (corrosion ~14.7k vs
glass_shatter ~477 / broken_lamp ~502). Head-class negatives dominate the BCE
gradient and suppress the tail classes. Seesaw BCE reweights negative-sample
gradients: the mitigation factor (`seesaw_p`) protects tail classes
(glass_shatter, broken_lamp) from corrosion gradient dominance, and the
compensation factor (`seesaw_q`) punishes confident false positives. This sweep
screens (p, q) on the 20% stratified subset before committing full-length runs.

## Sweep grid

| Run | seesaw_p | seesaw_q | Config |
|---|---:|---:|---|
{grid_rows}

Common config: yolo_seg_subset, 25 epochs, imgsz 1024, batch 8, AdamW, lr0 0.001,
freeze 23 + surgical early_texture unfreeze, model_preset
`model5_resume_adapt/model1_remapped_7class_init.pt`.

## Commands

```bash
{chr(10).join(commands)}
```

## Results (to fill after sweep)

| p | q | mAP50 | broken_lamp | glass_shatter | disjoint_part | scratch | crack | dent | corrosion | FPR |
|---|---|---|---|---|---|---|---|---|---|---|
{result_rows}
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(f"\nWrote {len(runs)} configs to {CFG_DIR.relative_to(ROOT)}/")
    print(f"Wrote report to {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
