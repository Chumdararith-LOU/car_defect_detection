
# Car Defect Detection: Model Selection and Benchmark Report

**Date:** 2026-08-05
**Project:** `car_defect_detection`
**Task:** Instance segmentation of car surface defects
**Final recommended model:** Model 5 Stage 1 Extended, 7-class
**Primary metric:** Mask mAP50

---

## 1. Executive Summary

This report compares the main experiments from the car defect detection project and selects the final model for production use.

The best model is:

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended
```

This model achieved:

- **Validation Mask mAP50:** 0.651
- **Test Mask mAP50:** 0.650
- **Test Mask mAP50-95:** 0.494
- **Test Mask Precision:** 0.666
- **Test Mask Recall:** 0.635

The near-identical validation and test performance shows excellent generalization and very little overfitting.

Compared with the strongest 7-class Model 4 control baseline, which reached **0.424 test Mask mAP50**, the final model improves performance by:

```text
0.650 - 0.424 = +0.226 Mask mAP50
```

This is a major improvement and demonstrates that the Resume-and-Adapt transfer-learning strategy, combined with the corrected 7-class taxonomy, was essential for this dataset.

---

## 2. Final Model Recommendation

The recommended production model is:

```text
Model 5 Stage 1 Extended, 7-class
```

Run folder:

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended
```

Weights:

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt
```

Key configuration:

| Parameter | Value |
|---|---:|
| Starting weights | `model1_remapped_7class_init.pt` |
| Dataset | 7-class clean dataset |
| Image size | 1024 |
| Epochs configured | 100 |
| Best epoch | 78 |
| Batch size | 4 |
| Initial LR | 0.005 |
| Freeze | 23 |
| Multi-scale | False |
| Mosaic | 0.0 |
| Scale augmentation | 0.3 |
| Rotation augmentation | 15.0 |
| Patience | 30 |

This model keeps the backbone frozen and trains only the adapted segmentation head. This strategy preserved the useful features learned by Model 1 while allowing the new 7-class head to converge properly.

---

## 3. Dataset and Task Definition

The final production task uses a 7-class defect taxonomy:

| Class ID | Class Name |
|---:|---|
| 0 | dent |
| 1 | scratch |
| 2 | crack |
| 3 | glass_shatter |
| 4 | broken_lamp |
| 5 | corrosion |
| 6 | disjoint_part |

The original 8-class schema contained separate `dent` and `deform` classes. These were merged because visual inspection showed that they were highly similar, with `deform` generally representing a more severe dent.

The merged 7-class schema produced a large performance improvement.

---

## 4. Main Benchmark Results

The following table compares the six selected report models.

Validation metrics are taken from the best epoch during training. Test metrics were computed by running each model’s `best.pt` on the held-out test split.

| Model | Strategy | Val Mask mAP50 | Val Mask mAP50-95 | Test Mask mAP50 | Test Mask mAP50-95 | Test Precision | Test Recall |
|---|---|---:|---:|---:|---:|---:|---:|
| 1. Baseline freeze 7-class | Model 4 control, freeze 15 | 0.414 | 0.269 | 0.392 | 0.248 | 0.421 | 0.454 |
| 2. Baseline unfreeze 7-class | Model 4 control, full unfreeze | 0.400 | 0.265 | 0.424 | 0.282 | 0.477 | 0.420 |
| 3. Model 5 Stage 2 8-class | Resume-and-Adapt, 8-class | 0.514 | 0.395 | 0.529 | 0.406 | 0.628 | 0.548 |
| 4. Model 5 Stage 1 7-class, 15 epochs | Resume-and-Adapt, head warmup | 0.622 | 0.476 | 0.639 | 0.496 | 0.795 | 0.588 |
| 5. Model 5 Stage 2 7-class | Resume-and-Adapt, differential fine-tune | 0.615 | 0.465 | 0.633 | 0.479 | 0.789 | 0.596 |
| **6. Champion: Model 5 Stage 1 Extended 7-class** | **Resume-and-Adapt, extended head warmup** | **0.651** | **0.487** | **0.650** | **0.494** | **0.666** | **0.635** |

---

## 5. Generalization Check

The following table compares validation Mask mAP50 and test Mask mAP50.

| Model | Val Mask mAP50 | Test Mask mAP50 | Test minus Val |
|---|---:|---:|---:|
| 1. Baseline freeze 7-class | 0.414 | 0.392 | -0.022 |
| 2. Baseline unfreeze 7-class | 0.400 | 0.424 | +0.024 |
| 3. Model 5 Stage 2 8-class | 0.514 | 0.529 | +0.015 |
| 4. Model 5 Stage 1 7-class, 15 epochs | 0.622 | 0.639 | +0.017 |
| 5. Model 5 Stage 2 7-class | 0.615 | 0.633 | +0.018 |
| **6. Champion: Model 5 Stage 1 Extended 7-class** | **0.651** | **0.650** | **-0.001** |

The champion model has almost no validation-test gap:

```text
0.651 validation
0.650 test
```

This is a very strong sign that the model is not overfitting and should behave consistently on new, unseen vehicles.

---

## 6. Key Findings

### 6.1 COCO-weight baselines are not strong enough

The Model 4 control experiments used standard pretrained YOLO segmentation weights.

The best 7-class control baseline was:

```text
model4_control_no_multiscale_7cls_unfreeze
```

It reached:

```text
Test Mask mAP50 = 0.424
```

This is far below the final champion model:

```text
Test Mask mAP50 = 0.650
```

Therefore, training from generic COCO weights is not sufficient for this industrial defect-detection task.

---

### 6.2 Resume-and-Adapt transfer learning is essential

The 8-class Resume-and-Adapt model reached:

```text
Test Mask mAP50 = 0.529
```

This already outperformed the best control baseline by:

```text
0.529 - 0.424 = +0.105 Mask mAP50
```

This shows that transferring the Model 1 backbone into the new task provided a strong advantage.

---

### 6.3 The 7-class taxonomy was a major improvement

After merging `dent` and `deform`, the 7-class head-warmup model reached:

```text
Test Mask mAP50 = 0.639
```

This is a large improvement over the 8-class model:

```text
0.639 - 0.529 = +0.110 Mask mAP50
```

The taxonomy correction was therefore one of the most important decisions in the project.

---

### 6.4 Full fine-tuning did not improve the model

The 7-class Stage 2 differential fine-tuning model reached:

```text
Validation Mask mAP50 = 0.615
Test Mask mAP50 = 0.633
```

This is worse than the 7-class Stage 1 head-warmup model:

```text
Validation Mask mAP50 = 0.622
Test Mask mAP50 = 0.639
```

It is also worse than the extended Stage 1 champion:

```text
Validation Mask mAP50 = 0.651
Test Mask mAP50 = 0.650
```

The conclusion is that unfreezing the backbone on this relatively small dataset caused the model to damage useful pretrained features. For this dataset, head-only training was the better strategy.

---

### 6.5 Extending Stage 1 head warmup produced the best model

The original 7-class Stage 1 warmup was only 15 epochs long.

Extending it to 100 epochs with patience 30 improved the validation result from:

```text
0.622
```

to:

```text
0.651
```

The extended model also achieved the best test result:

```text
0.650
```

This confirms that the backbone should remain frozen while the new head is given enough epochs to converge.

---

## 7. Selected Model Details

The final selected model is:

```text
stage1_head_warmup_7cls_extended
```

### 7.1 Performance

| Metric | Value |
|---|---:|
| Best validation Mask mAP50 | 0.651 |
| Best validation epoch | 78 |
| Final validation Mask mAP50 | 0.643 |
| Test Mask mAP50 | 0.650 |
| Test Mask mAP50-95 | 0.494 |
| Test Mask Precision | 0.666 |
| Test Mask Recall | 0.635 |

### 7.2 Why this model was selected

This model was selected because it has:

1. The highest validation Mask mAP50 among all compared models.
2. The highest test Mask mAP50 among all compared models.
3. Excellent generalization with almost no validation-test gap.
4. Stable training behavior.
5. A simpler and safer training strategy than full fine-tuning.
6. Compatibility with the final 7-class production taxonomy.

---

## 8. Visual Results

The following plots were gathered into:

```text
reports/assets/
```

Each folder corresponds to one selected model.

---

### 8.1 Baseline freeze 7-class

Run:

```text
car_defect_detection/model4_control_no_multiscale_7cls
```

Confusion matrix:

![Baseline freeze confusion matrix](assets/1_baseline_freeze_7cls/confusion_matrix_normalized.png)

Mask PR curve:

![Baseline freeze Mask PR curve](assets/1_baseline_freeze_7cls/MaskPR_curve.png)

Training results:

![Baseline freeze results](assets/1_baseline_freeze_7cls/results.png)

---

### 8.2 Baseline unfreeze 7-class

Run:

```text
car_defect_detection/model4_control_no_multiscale_7cls_unfreeze
```

Confusion matrix:

![Baseline unfreeze confusion matrix](assets/2_baseline_unfreeze_7cls/confusion_matrix_normalized.png)

Mask PR curve:

![Baseline unfreeze Mask PR curve](assets/2_baseline_unfreeze_7cls/MaskPR_curve.png)

Training results:

![Baseline unfreeze results](assets/2_baseline_unfreeze_7cls/results.png)

---

### 8.3 Model 5 Stage 2 8-class

Run:

```text
model5_resume_adapt/stage2_differential_finetune-5
```

Confusion matrix:

![Model 5 8-class confusion matrix](assets/3_model5_stage2_8cls/confusion_matrix_normalized.png)

Mask PR curve:

![Model 5 8-class Mask PR curve](assets/3_model5_stage2_8cls/MaskPR_curve.png)

Training results:

![Model 5 8-class results](assets/3_model5_stage2_8cls/results.png)

---

### 8.4 Model 5 Stage 1 7-class, 15 epochs

Run:

```text
model5_resume_adapt_7cls/stage1_head_warmup_7cls
```

Confusion matrix:

![Model 5 Stage 1 7-class confusion matrix](assets/4_model5_stage1_7cls_15ep/confusion_matrix_normalized.png)

Mask PR curve:

![Model 5 Stage 1 7-class Mask PR curve](assets/4_model5_stage1_7cls_15ep/MaskPR_curve.png)

Training results:

![Model 5 Stage 1 7-class results](assets/4_model5_stage1_7cls_15ep/results.png)

---

### 8.5 Model 5 Stage 2 7-class

Run:

```text
model5_resume_adapt_7cls/stage2_differential_finetune_7cls
```

Confusion matrix:

![Model 5 Stage 2 7-class confusion matrix](assets/5_model5_stage2_7cls_forgetting/confusion_matrix_normalized.png)

Mask PR curve:

![Model 5 Stage 2 7-class Mask PR curve](assets/5_model5_stage2_7cls_forgetting/MaskPR_curve.png)

Training results:

![Model 5 Stage 2 7-class results](assets/5_model5_stage2_7cls_forgetting/results.png)

---

### 8.6 Champion: Model 5 Stage 1 Extended 7-class

Run:

```text
stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended
```

Confusion matrix:

![Champion confusion matrix](assets/6_champion_extended_7cls/confusion_matrix_normalized.png)

Mask PR curve:

![Champion Mask PR curve](assets/6_champion_extended_7cls/MaskPR_curve.png)

Training results:

![Champion results](assets/6_champion_extended_7cls/results.png)

---

## 9. Legacy Baselines to Verify

The following two baseline runs were intentionally kept, but their metrics are not yet included in the main benchmark table:

```text
runs/segment/car_defect_detection/yolo26m_1024_stage2_baseline-8
runs/segment/car_defect_detection/yolo26m_1024_stage2_baseline_dataset-2
```

These should be checked next.

Possible next step:

1. Extract their validation metrics from `results.csv`.
2. Run test-set evaluation using their `best.pt`.
3. Decide whether they belong in the main baseline table or in an appendix.

---

## 10. Limitations and Remaining Challenges

### 10.1 Rare classes remain difficult

The classes `corrosion` and `disjoint_part` remain the most difficult classes because they have far fewer training and validation examples than the dominant classes.

Previous diagnostic work showed that small corrosion defects can be lost during global resizing. Sliced inference at native resolution can help recover some of these defects.

### 10.2 Precision depends on deployment threshold

The champion model has strong mAP performance, but the final operating precision and recall will depend on the confidence threshold used during deployment.

For production use, threshold presets should be selected according to the desired trade-off:

| Preset | Purpose |
|---|---|
| Balanced | Default inspection mode |
| Safety | Higher recall, more false positives tolerated |
| Max Recall | Auditing mode, maximum detection sensitivity |

### 10.3 More rare-class data is needed

The long-term solution for weak rare classes is not only inference tuning. The dataset needs more confirmed examples of:

- `corrosion`
- `disjoint_part`

A data flywheel should be used after deployment:

1. Log operator-rejected false positives as hard negatives.
2. Log confirmed rare defects as hard positives.
3. Retrain Model 6 using the expanded dataset.

---

## 11. Conclusion

The final recommended model is:

```text
stage1_head_warmup_7cls_extended
```

It achieved:

```text
Validation Mask mAP50 = 0.651
Test Mask mAP50 = 0.650
```

This model outperforms all baselines and ablations by a large margin.

The main lessons from this project are:

1. Generic COCO pretrained weights are not sufficient for this task.
2. Transferring the Model 1 backbone is highly valuable.
3. Merging `dent` and `deform` into one class significantly improved performance.
4. Head-only warmup outperformed full fine-tuning on this small dataset.
5. Extending the head-only warmup produced the best and most stable model.
6. The final model generalizes well to the held-out test set.

---

## Appendix A: Selected Model Paths

| Short name | Run folder |
|---|---|
| 1_baseline_freeze_7cls | `runs/segment/car_defect_detection/model4_control_no_multiscale_7cls` |
| 2_baseline_unfreeze_7cls | `runs/segment/car_defect_detection/model4_control_no_multiscale_7cls_unfreeze` |
| 3_model5_stage2_8cls | `runs/segment/model5_resume_adapt/stage2_differential_finetune-5` |
| 4_model5_stage1_7cls_15ep | `runs/segment/model5_resume_adapt_7cls/stage1_head_warmup_7cls` |
| 5_model5_stage2_7cls_forgetting | `runs/segment/model5_resume_adapt_7cls/stage2_differential_finetune_7cls` |
| 6_champion_extended_7cls | `runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended` |
