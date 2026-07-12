# 📊 Experiment Report: `yolo26n_car_defect_detection`

> **Project:** car_defect_detection_test2
> **Generated:** 2026-07-12 14:33:56
> **Git Commit:** `084b5e8`
> **MLflow Run ID:** `e4514a8012f446b9a1110fa17180797c`

---

## 🎯 Executive Summary

```{admonition} Key Performance Indicators
:class: tip









| Metric | Bounding Box | Segmentation Mask |
| :--- | :---: | :---: |
| **Precision** | `—` | `—` |
| **Recall** | `—` | `—` |
| **mAP@50** | `—` | `—` |
| **mAP@50-95** | `—` | `—` |
```

---

## 🏗️ Training Configuration

### Core Architecture

| Parameter | Value |
| :--- | :--- |
| Model Preset | `—` |
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
| Precision | `—` |
| Recall | `—` |
| mAP@50 | `—` |
| mAP@50-95 | `—` |

### Instance Segmentation Masks

| Metric | Score |
| :--- | :--- |
| Precision | `—` |
| Recall | `—` |
| mAP@50 | `—` |
| mAP@50-95 | `—` |

### Final Training Losses

| Loss Component | Train (Final) | Validation (Final) |
| :--- | :---: | :---: |
| Box Loss | `1.58927` | `1.70118` |
| Segmentation Loss | `2.80056` | `1.77572` |
| Classification Loss | `2.86155` | `2.98302` |
| DFL Loss | `0.03163` | `0.04073` |

---

## 🖼️ Visualizations



*No visual artifacts were found for this run.*



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
