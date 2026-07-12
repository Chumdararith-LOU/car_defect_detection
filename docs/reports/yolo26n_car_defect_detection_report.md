# 📊 Experiment Report: yolo26n_car_defect_detection

**Project:** car_defect_detection_test2
**Date Generated:** 2026-07-12 13:12:24
**Git Commit Lineage:** `084b5e8`

---

## ⚙️ Model & Hyperparameters
*This section dynamically lists the parameters used for this specific run.*

| Parameter | Value |
| :--- | :--- |

| `config_blueprint` | configs/train/yolo26n-seg.yaml |

| `task` | segment |

| `mode` | train |

| `model` | yolo26n-seg.pt |

| `data` | data/processed/Experiment_v1/data.yaml |

| `epochs` | 5 |

| `time` | None |

| `patience` | 100 |

| `batch` | 32 |

| `imgsz` | 640 |

| `save` | True |

| `save_period` | -1 |

| `cache` | False |

| `device` | 0 |

| `workers` | 8 |

| `project` | car_defect_detection_test2 |

| `name` | yolo26n_car_defect_detection |

| `exist_ok` | False |

| `pretrained` | True |

| `optimizer` | auto |

| `verbose` | True |

| `seed` | 42 |

| `deterministic` | True |

| `single_cls` | False |

| `rect` | False |

| `cos_lr` | False |

| `close_mosaic` | 10 |

| `resume` | False |

| `amp` | True |

| `fraction` | 1.0 |

| `profile` | False |

| `freeze` | None |

| `multi_scale` | 0.0 |

| `compile` | False |

| `overlap_mask` | True |

| `mask_ratio` | 4 |

| `dropout` | 0.0 |

| `val` | True |

| `split` | val |

| `save_json` | False |

| `conf` | None |

| `iou` | 0.7 |

| `max_det` | 300 |

| `quantize` | None |

| `dnn` | False |

| `plots` | True |

| `end2end` | None |

| `source` | None |

| `vid_stride` | 1 |

| `stream_buffer` | False |

| `visualize` | False |

| `augment` | False |

| `agnostic_nms` | False |

| `classes` | None |

| `retina_masks` | False |

| `embed` | None |

| `show` | False |

| `save_frames` | False |

| `save_txt` | False |

| `save_conf` | False |

| `save_crop` | False |

| `show_labels` | True |

| `show_conf` | True |

| `show_boxes` | True |

| `line_width` | None |

| `format` | torchscript |

| `keras` | False |

| `optimize` | False |

| `dynamic` | False |

| `simplify` | True |

| `opset` | None |

| `workspace` | None |

| `nms` | False |

| `lr0` | 0.01 |

| `lrf` | 0.01 |

| `momentum` | 0.937 |

| `weight_decay` | 0.0005 |

| `warmup_epochs` | 3.0 |

| `warmup_momentum` | 0.8 |

| `warmup_bias_lr` | 0.0 |

| `distill_model` | None |

| `dis` | 6.0 |

| `box` | 7.5 |

| `cls` | 0.5 |

| `cls_pw` | 0.0 |

| `dfl` | 1.5 |

| `pose` | 12.0 |

| `kobj` | 1.0 |

| `rle` | 1.0 |

| `angle` | 1.0 |

| `nbs` | 64 |

| `hsv_h` | 0.03 |

| `hsv_s` | 0.7 |

| `hsv_v` | 0.5 |

| `degrees` | 10.0 |

| `translate` | 0.1 |

| `scale` | 0.5 |

| `shear` | 0.0 |

| `perspective` | 0.0005 |

| `flipud` | 0.0 |

| `fliplr` | 0.5 |

| `bgr` | 0.0 |

| `mosaic` | 0.3 |

| `mixup` | 0.1 |

| `cutmix` | 0.0 |

| `copy_paste` | 0.0 |

| `copy_paste_mode` | flip |

| `auto_augment` | randaugment |

| `erasing` | 0.4 |

| `cfg` | None |

| `tracker` | tracktrack.yaml |

| `save_dir` | /home/lamacpp/secure_workspace/car_defect_detection/runs/segment/car_defect_detection_test2/yolo26n_car_defect_detection |


---

## 📈 Final Evaluation Metrics
*These metrics were automatically pulled from the MLflow tracking server.*

| Metric | Score |
| :--- | :--- |

| **system/cpu_utilization_percentage** | `12.0` |

| **system/system_memory_usage_megabytes** | `19915.4` |

| **system/system_memory_usage_percentage** | `59.6` |

| **system/disk_usage_percentage** | `88.3` |

| **system/disk_usage_megabytes** | `843750.1` |

| **system/disk_available_megabytes** | `111500.6` |

| **system/network_receive_megabytes** | `1.8063` |

| **system/network_transmit_megabytes** | `1.431` |

| **system/gpu_0_memory_usage_percentage** | `37.3` |

| **system/gpu_0_memory_usage_megabytes** | `9611.9` |

| **system/gpu_0_utilization_percentage** | `85.0` |

| **system/gpu_0_power_usage_watts** | `234.6` |

| **system/gpu_0_power_usage_percentage** | `45.5` |

| **lr/pg0** | `0.0002` |

| **lr/pg1** | `0.0002` |

| **lr/pg2** | `0.0002` |

| **train/box_loss** | `1.5893` |

| **train/seg_loss** | `2.8006` |

| **train/cls_loss** | `2.8615` |

| **train/dfl_loss** | `0.0316` |

| **train/sem_loss** | `2.2845` |

| **metrics/precisionB** | `0.6` |

| **metrics/recallB** | `0.4696` |

| **metrics/mAP50B** | `0.5211` |

| **metrics/mAP50-95B** | `0.2598` |

| **metrics/precisionM** | `0.6042` |

| **metrics/recallM** | `0.4744` |

| **metrics/mAP50M** | `0.5168` |

| **metrics/mAP50-95M** | `0.2822` |

| **val/box_loss** | `1.7012` |

| **val/seg_loss** | `1.7757` |

| **val/cls_loss** | `2.983` |

| **val/dfl_loss** | `0.0407` |

| **val/sem_loss** | `0.0` |


---

## 🖼️ Visualizations & Artifacts
*Below are the evaluation curves and matrices generated during training.*


<div align="center">

  <img src="../../reports/figures/yolo26n_car_defect_detection/results.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/MaskF1_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/train_batch0.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/MaskR_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/train_batch2.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/val_batch0_pred.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/MaskP_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/BoxF1_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/val_batch2_pred.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/BoxP_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/val_batch0_labels.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/confusion_matrix_normalized.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/confusion_matrix.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/BoxPR_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/train_batch1.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/val_batch1_labels.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/val_batch1_pred.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/BoxR_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/val_batch2_labels.jpg" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/MaskPR_curve.png" width="45%" style="margin: 10px;">

  <img src="../../reports/figures/yolo26n_car_defect_detection/labels.jpg" width="45%" style="margin: 10px;">

</div>
