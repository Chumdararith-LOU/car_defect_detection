# Phase 2: Seesaw Loss Hyperparameter Sweep Plan

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
| 1 | 0.6 | 1.5 | configs/train/stage2/seesaw_sweep_p06_q15.yaml |
| 2 | 0.6 | 2.0 | configs/train/stage2/seesaw_sweep_p06_q20.yaml |
| 3 | 0.6 | 2.5 | configs/train/stage2/seesaw_sweep_p06_q25.yaml |
| 4 | 0.8 | 1.5 | configs/train/stage2/seesaw_sweep_p08_q15.yaml |
| 5 | 0.8 | 2.0 | configs/train/stage2/seesaw_sweep_p08_q20.yaml |
| 6 | 0.8 | 2.5 | configs/train/stage2/seesaw_sweep_p08_q25.yaml |
| 7 | 1.0 | 1.5 | configs/train/stage2/seesaw_sweep_p10_q15.yaml |
| 8 | 1.0 | 2.0 | configs/train/stage2/seesaw_sweep_p10_q20.yaml |
| 9 | 1.0 | 2.5 | configs/train/stage2/seesaw_sweep_p10_q25.yaml |

Common config: yolo_seg_subset, 25 epochs, imgsz 1024, batch 8, AdamW, lr0 0.001,
freeze 23 + surgical early_texture unfreeze, model_preset
`model5_resume_adapt/model1_remapped_7class_init.pt`.

## Commands

```bash
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p06_q15.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p06_q20.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p06_q25.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p08_q15.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p08_q20.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p08_q25.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p10_q15.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p10_q20.yaml
python src/train/train.py --config configs/train/stage2/seesaw_sweep_p10_q25.yaml
```

## Results (to fill after sweep)

| p | q | mAP50 | broken_lamp | glass_shatter | disjoint_part | scratch | crack | dent | corrosion | FPR |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.6 | 1.5 |  |  |  |  |  |  |  |  |  |
| 0.6 | 2.0 |  |  |  |  |  |  |  |  |  |
| 0.6 | 2.5 |  |  |  |  |  |  |  |  |  |
| 0.8 | 1.5 |  |  |  |  |  |  |  |  |  |
| 0.8 | 2.0 |  |  |  |  |  |  |  |  |  |
| 0.8 | 2.5 |  |  |  |  |  |  |  |  |  |
| 1.0 | 1.5 |  |  |  |  |  |  |  |  |  |
| 1.0 | 2.0 |  |  |  |  |  |  |  |  |  |
| 1.0 | 2.5 |  |  |  |  |  |  |  |  |  |
