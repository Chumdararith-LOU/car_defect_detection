# 📊 Experiment Report: `yolo26n_car_defect_detection`

> **Project:** car_defect_detection_test2
> **Generated:** 2026-07-12 15:03:49
> **Git Commit:** `084b5e8`
> **MLflow Run ID:** `e4514a8012f446b9a1110fa17180797c`

---

## 🎯 Executive Summary

```{admonition} Key Performance Indicators
:class: tip

| Metric | Bounding Box | Segmentation Mask |
| :--- | :---: | :---: |
| **Precision** | `0.6` | `0.6042` |
| **Recall** | `0.4696` | `0.4744` |
| **mAP@50** | `0.5211` | `0.5168` |
| **mAP@50-95** | `0.2598` | `0.2822` |
```

---

## 🏗️ Training Configuration

### Core Architecture

| Parameter | Value |
| :--- | :--- |
| Model Preset | `yolo26n-seg.pt` |
| Epochs | `5` |
| Batch Size | `32` |
| Image Size | `640` |
| Device | `0` |
| Workers | `8` |
| AMP (Mixed Precision) | `True` |
| Random Seed | `42` |

### Environmental Augmentations

| Augmentation | Value |
| :--- | :--- |
| HSV Hue | `0.03` |
| HSV Saturation | `0.7` |
| HSV Value | `0.5` |
| Degrees Rotation | `10.0` |
| Scale | `0.5` |
| Perspective | `0.0005` |
| Horizontal Flip | `0.5` |
| Mosaic | `0.3` |
| MixUp | `0.1` |
| Random Erasing | `0.4` |
| Close Mosaic (last N epochs) | `10` |

---

## 📈 Final Evaluation Metrics

### Bounding Box Detection

| Metric | Score |
| :--- | :--- |
| Precision | `0.6` |
| Recall | `0.4696` |
| mAP@50 | `0.5211` |
| mAP@50-95 | `0.2598` |

### Instance Segmentation Masks

| Metric | Score |
| :--- | :--- |
| Precision | `0.6042` |
| Recall | `0.4744` |
| mAP@50 | `0.5168` |
| mAP@50-95 | `0.2822` |

### Final Training Losses

| Loss Component | Train (Final) | Validation (Final) |
| :--- | :---: | :---: |
| Box Loss | `1.58927` | `1.70118` |
| Segmentation Loss | `2.80056` | `1.77572` |
| Classification Loss | `2.86155` | `2.98302` |
| DFL Loss | `0.03163` | `0.04073` |

---

## 🖼️ Visualizations


### 📊 Performance Curves

<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/MaskF1_curve.png" style="width: 100%;">
  <figcaption><em>Maskf1 Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/MaskR_curve.png" style="width: 100%;">
  <figcaption><em>Maskr Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/MaskP_curve.png" style="width: 100%;">
  <figcaption><em>Maskp Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/BoxF1_curve.png" style="width: 100%;">
  <figcaption><em>Boxf1 Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/BoxP_curve.png" style="width: 100%;">
  <figcaption><em>Boxp Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/BoxPR_curve.png" style="width: 100%;">
  <figcaption><em>Boxpr Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/BoxR_curve.png" style="width: 100%;">
  <figcaption><em>Boxr Curve</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/MaskPR_curve.png" style="width: 100%;">
  <figcaption><em>Maskpr Curve</em></figcaption>
</figure>

### 🎯 Confusion Analysis

<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="../figures/yolo26n_car_defect_detection/confusion_matrix_normalized.png" style="width: 100%;">
  <figcaption><em>Confusion Matrix Normalized</em></figcaption>
</figure>
<figure style="display: inline-block; width: 48%; margin: 5px; text-align: center;">
  <img src="../figures/yolo26n_car_defect_detection/confusion_matrix.png" style="width: 100%;">
  <figcaption><em>Confusion Matrix</em></figcaption>
</figure>

### 🖼️ Training Overview

<figure style="text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/results.png" style="width: 100%; max-width: 1000px;">
  <figcaption><em>Combined Training Curves — Loss & Metrics across all Epochs</em></figcaption>
</figure>

### 🔬 Sample Predictions

<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/train_batch0.jpg" style="width: 100%;">
  <figcaption><em>Train Batch0</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/train_batch2.jpg" style="width: 100%;">
  <figcaption><em>Train Batch2</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/val_batch0_pred.jpg" style="width: 100%;">
  <figcaption><em>Val Batch0 Pred</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/val_batch2_pred.jpg" style="width: 100%;">
  <figcaption><em>Val Batch2 Pred</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/val_batch0_labels.jpg" style="width: 100%;">
  <figcaption><em>Val Batch0 Labels</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/train_batch1.jpg" style="width: 100%;">
  <figcaption><em>Train Batch1</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/val_batch1_labels.jpg" style="width: 100%;">
  <figcaption><em>Val Batch1 Labels</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/val_batch1_pred.jpg" style="width: 100%;">
  <figcaption><em>Val Batch1 Pred</em></figcaption>
</figure>
<figure style="display: inline-block; width: 32%; margin: 3px; text-align: center;">
  <img src="figures/yolo26n_car_defect_detection/val_batch2_labels.jpg" style="width: 100%;">
  <figcaption><em>Val Batch2 Labels</em></figcaption>
</figure>


---

## 🔗 Reproducibility & Lineage

```{admonition} Traceability Metadata
:class: important

| Attribute | Value |
| :--- | :--- |
| **MLflow Run ID** | `e4514a8012f446b9a1110fa17180797c` |
| **Git Commit** | `084b5e8` |
| **Configuration Blueprint** | `configs/train/yolo26n-seg.yaml` |
| **Report Generator** | `src/eval/validate.py` |
| **Template** | `reports/templates/experiment_report.md.j2` |
```
