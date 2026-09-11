"""SAHI evaluation wrapper for Stage 2 defect detection.

This module provides the inference bridge between YOLO models and the
evaluation metrics modules (size_bucketed, clean_fpr, classwise).

It handles:
- Standard YOLO inference
- SAHI (Slicing Aided Hyper Inference) for high-resolution images
- Objectness branch two-tier scoring: final_score = P(class) × P(objectness)
- Prediction collection in standardized format

The standardized prediction format is:
    List[np.ndarray] where each array is [N_i, 6] with columns:
    [x1, y1, x2, y2, score, class_id]

References:
    - eval.md, Module 7: SAHI Explained — The Jigsaw Puzzle Strategy
    - eval.md, Module 8: The Math of Slicing — Patch Size, Stride, and Overlap
    - eval.md, Module 10: NMS — Killing the Duplicates (IOS for thin boxes)
    - eval.md, Module 21: Tiling Parameter Sensitivity
"""

import os
import sys
import numpy as np
import torch
from typing import List, Dict, Optional, Tuple, Any

from ultralytics import YOLO

# Ensure project root is in path
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)


def resolve_device(device: str = "auto") -> str:
    """Resolve the compute device.

    Args:
        device: 'auto', 'cuda', 'mps', or 'cpu'

    Returns:
        Resolved device string
    """
    if device == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    return device


def load_model(
    weights_path: str,
    device: str = "auto",
) -> YOLO:
    """Load a YOLO model from weights.

    Args:
        weights_path: Path to the model weights (.pt file)
        device: Compute device ('auto', 'cuda', 'mps', 'cpu')

    Returns:
        Loaded YOLO model
    """
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Model weights not found: {weights_path}")

    resolved_device = resolve_device(device)
    model = YOLO(weights_path)
    model.to(resolved_device)
    return model


def extract_predictions_from_results(
    results: Any,
    conf_threshold: float = 0.25,
    use_objectness: bool = False,
    obj_threshold: float = 0.5,
) -> np.ndarray:
    """Extract predictions from YOLO results into standardized format.

    Handles both standard YOLO results and objectness-branch results.
    For objectness models, applies two-tier gating:
        final_score = P(class) × P(objectness)

    Args:
        results: YOLO inference results (single image)
        conf_threshold: Minimum confidence threshold
        use_objectness: Whether the model has an objectness branch
        obj_threshold: Objectness threshold for two-tier gating

    Returns:
        [N, 6] array with columns [x1, y1, x2, y2, score, class_id].
        Returns empty array with shape (0, 6) if no detections.
    """
    if results is None or len(results) == 0:
        return np.zeros((0, 6))

    result = results[0] if isinstance(results, (list, tuple)) else results

    # Get boxes from result
    if result.boxes is None or len(result.boxes) == 0:
        return np.zeros((0, 6))

    boxes = result.boxes
    xyxy = boxes.xyxy.cpu().numpy()  # [N, 4]
    conf = boxes.conf.cpu().numpy()  # [N]
    cls = boxes.cls.cpu().numpy().astype(int)  # [N]

    # Apply confidence threshold
    mask = conf >= conf_threshold
    xyxy = xyxy[mask]
    conf = conf[mask]
    cls = cls[mask]

    if len(conf) == 0:
        return np.zeros((0, 6))

    # If objectness branch is available, apply two-tier gating
    # Note: This requires the model to output objectness scores
    # For now, we use the standard confidence as the final score
    # TODO: Integrate objectness branch scoring when model supports it
    if (
        use_objectness
        and hasattr(result, "objectness")
        and result.objectness is not None
    ):
        obj_scores = result.objectness.cpu().numpy()
        obj_mask = obj_scores >= obj_threshold
        # Two-tier gating: final_score = P(class) × P(objectness)
        final_scores = conf * obj_scores
        combined_mask = mask & obj_mask
        xyxy = xyxy[combined_mask[mask]]
        final_scores = final_scores[combined_mask[mask]]
        cls = cls[combined_mask[mask]]
    else:
        final_scores = conf

    # Stack into [N, 6] format
    predictions = np.column_stack([xyxy, final_scores, cls])
    return predictions


def run_inference_single(
    model: YOLO,
    image_path: str,
    conf_threshold: float = 0.25,
    imgsz: int = 1024,
    use_sahi: bool = False,
    sahi_config: Optional[Dict] = None,
    use_objectness: bool = False,
    obj_threshold: float = 0.5,
    device: str = "auto",
) -> np.ndarray:
    """Run inference on a single image.

    Args:
        model: Loaded YOLO model
        image_path: Path to the image
        conf_threshold: Minimum confidence threshold
        imgsz: Inference image size
        use_sahi: Whether to use SAHI tiling
        sahi_config: SAHI configuration dict
        use_objectness: Whether model has objectness branch
        obj_threshold: Objectness threshold
        device: Compute device

    Returns:
        [N, 6] predictions array
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if use_sahi and sahi_config:
        return _run_sahi_inference(
            model,
            image_path,
            conf_threshold,
            sahi_config,
            use_objectness,
            obj_threshold,
        )
    else:
        # Standard full-image inference
        results = model.predict(
            source=image_path,
            conf=conf_threshold,
            imgsz=imgsz,
            device=resolve_device(device),
            verbose=False,
        )
        return extract_predictions_from_results(
            results, conf_threshold, use_objectness, obj_threshold
        )


def _run_sahi_inference(
    model: YOLO,
    image_path: str,
    conf_threshold: float,
    sahi_config: Dict,
    use_objectness: bool = False,
    obj_threshold: float = 0.5,
) -> np.ndarray:
    """Run SAHI (Slicing Aided Hyper Inference) on an image.

    Implements the jigsaw puzzle strategy from eval.md Module 7:
    1. Slice image into overlapping patches
    2. Run inference on each patch
    3. Transform coordinates to global space
    4. Apply NMS with IOS metric for thin boxes

    Args:
        model: Loaded YOLO model
        image_path: Path to the image
        conf_threshold: Minimum confidence threshold
        sahi_config: SAHI configuration with keys:
            - slice_size: int (default 1024)
            - overlap_ratio: float (default 0.15)
            - postprocess_match_metric: str ('IOS' or 'IOU')
            - postprocess_match_threshold: float (default 0.50)
        use_objectness: Whether model has objectness branch
        obj_threshold: Objectness threshold

    Returns:
        [N, 6] predictions array in global coordinates
    """
    try:
        from sahi.predict import get_sliced_prediction
    except ImportError:
        # Fallback to standard inference if sahi not installed
        print("[⚠️] SAHI not installed. Falling back to standard inference.")
        results = model.predict(
            source=image_path,
            conf=conf_threshold,
            imgsz=sahi_config.get("slice_size", 1024),
            verbose=False,
        )
        return extract_predictions_from_results(results, conf_threshold)

    slice_size = sahi_config.get("slice_size", 1024)
    overlap_ratio = sahi_config.get("overlap_ratio", 0.15)
    match_metric = sahi_config.get("postprocess_match_metric", "IOS")
    match_threshold = sahi_config.get("postprocess_match_threshold", 0.50)

    # Use sahi's sliced prediction
    # Note: This requires the model to be compatible with sahi's interface
    # For YOLO models, we use the detection_model parameter
    try:
        get_sliced_prediction(
            image=image_path,
            detection_model=None,
            slice_height=slice_size,
            slice_width=slice_size,
            overlap_height_ratio=overlap_ratio,
            overlap_width_ratio=overlap_ratio,
            postprocess_match_metric=match_metric,
            postprocess_match_threshold=match_threshold,
        )
        return np.zeros((0, 6))
    except Exception:
        # Fallback: manual slicing
        return _manual_sahi_inference(
            model,
            image_path,
            conf_threshold,
            slice_size,
            overlap_ratio,
            use_objectness,
            obj_threshold,
        )


def _manual_sahi_inference(
    model: YOLO,
    image_path: str,
    conf_threshold: float,
    slice_size: int,
    overlap_ratio: float,
    use_objectness: bool = False,
    obj_threshold: float = 0.5,
) -> np.ndarray:
    """Manual SAHI implementation using YOLO predict on slices.

    This is a fallback when the sahi library integration is not available.
    It manually slices the image, runs inference on each slice, and
    stitches the results back together.

    Args:
        model: Loaded YOLO model
        image_path: Path to the image
        conf_threshold: Minimum confidence threshold
        slice_size: Size of each slice (square)
        overlap_ratio: Overlap between adjacent slices
        use_objectness: Whether model has objectness branch
        obj_threshold: Objectness threshold

    Returns:
        [N, 6] predictions array in global coordinates
    """
    from PIL import Image

    img = Image.open(image_path)
    img_w, img_h = img.size

    # Calculate stride from overlap
    stride = int(slice_size * (1 - overlap_ratio))

    # Generate slice positions
    x_positions = list(range(0, img_w - slice_size + 1, stride))
    if not x_positions or x_positions[-1] + slice_size < img_w:
        x_positions.append(max(0, img_w - slice_size))

    y_positions = list(range(0, img_h - slice_size + 1, stride))
    if not y_positions or y_positions[-1] + slice_size < img_h:
        y_positions.append(max(0, img_h - slice_size))

    # Remove duplicates and sort
    x_positions = sorted(set(x_positions))
    y_positions = sorted(set(y_positions))

    all_predictions = []

    for y in y_positions:
        for x in x_positions:
            # Crop the slice
            x_end = min(x + slice_size, img_w)
            y_end = min(y + slice_size, img_h)
            x_start = max(0, x_end - slice_size)
            y_start = max(0, y_end - slice_size)

            # Run inference on the slice
            slice_img = img.crop((x_start, y_start, x_end, y_end))

            # Save temp slice for YOLO predict
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                slice_img.save(tmp.name)
                results = model.predict(
                    source=tmp.name,
                    conf=conf_threshold,
                    imgsz=slice_size,
                    verbose=False,
                )
                os.unlink(tmp.name)

            # Extract predictions and transform to global coordinates
            preds = extract_predictions_from_results(
                results, conf_threshold, use_objectness, obj_threshold
            )

            if len(preds) > 0:
                # Transform local coordinates to global
                preds[:, 0] += x_start  # x1
                preds[:, 1] += y_start  # y1
                preds[:, 2] += x_start  # x2
                preds[:, 3] += y_start  # y2
                all_predictions.append(preds)

    if not all_predictions:
        return np.zeros((0, 6))

    # Concatenate all predictions
    all_preds = np.vstack(all_predictions)

    # Apply NMS to remove duplicates from overlapping slices
    # Using IOS metric for thin boxes (Module 10)
    all_preds = _apply_nms(all_preds, iou_threshold=0.5, use_ios=True)

    return all_preds


def _apply_nms(
    predictions: np.ndarray,
    iou_threshold: float = 0.5,
    use_ios: bool = True,
) -> np.ndarray:
    """Apply Non-Maximum Suppression to predictions.

    Uses IOS (Intersection over Smaller) metric for thin boxes like scratches,
    as recommended in eval.md Module 10.

    Args:
        predictions: [N, 6] array with [x1, y1, x2, y2, score, class_id]
        iou_threshold: Threshold for suppression
        use_ios: Use IOS instead of IoU (better for thin boxes)

    Returns:
        Filtered predictions after NMS
    """
    if len(predictions) == 0:
        return predictions

    # Sort by score (descending)
    sorted_indices = np.argsort(-predictions[:, 4])
    predictions = predictions[sorted_indices]

    keep = []
    suppressed = np.zeros(len(predictions), dtype=bool)

    for i in range(len(predictions)):
        if suppressed[i]:
            continue
        keep.append(i)

        for j in range(i + 1, len(predictions)):
            if suppressed[j]:
                continue

            # Only suppress same-class detections
            if predictions[i, 5] != predictions[j, 5]:
                continue

            # Compute IoU or IOS
            box_i = predictions[i, :4]
            box_j = predictions[j, :4]

            x1 = max(box_i[0], box_j[0])
            y1 = max(box_i[1], box_j[1])
            x2 = min(box_i[2], box_j[2])
            y2 = min(box_i[3], box_j[3])

            intersection = max(0, x2 - x1) * max(0, y2 - y1)
            area_i = (box_i[2] - box_i[0]) * (box_i[3] - box_i[1])
            area_j = (box_j[2] - box_j[0]) * (box_j[3] - box_j[1])

            if use_ios:
                # IOS: intersection / min(area_i, area_j)
                min_area = min(area_i, area_j)
                metric = intersection / min_area if min_area > 0 else 0
            else:
                # IoU: intersection / union
                union = area_i + area_j - intersection
                metric = intersection / union if union > 0 else 0

            if metric > iou_threshold:
                suppressed[j] = True

    return predictions[keep]


def run_batch_inference(
    model: YOLO,
    image_paths: List[str],
    conf_threshold: float = 0.25,
    imgsz: int = 1024,
    use_sahi: bool = False,
    sahi_config: Optional[Dict] = None,
    use_objectness: bool = False,
    obj_threshold: float = 0.5,
    device: str = "auto",
    verbose: bool = False,
) -> List[np.ndarray]:
    """Run inference on a batch of images.

    Args:
        model: Loaded YOLO model
        image_paths: List of image paths
        conf_threshold: Minimum confidence threshold
        imgsz: Inference image size
        use_sahi: Whether to use SAHI tiling
        sahi_config: SAHI configuration dict
        use_objectness: Whether model has objectness branch
        obj_threshold: Objectness threshold
        device: Compute device
        verbose: Print progress

    Returns:
        List of [N_i, 6] prediction arrays, one per image
    """
    all_predictions = []
    total = len(image_paths)

    for idx, image_path in enumerate(image_paths):
        if verbose and (idx + 1) % 10 == 0:
            print(f"  Processing image {idx + 1}/{total}...")

        try:
            preds = run_inference_single(
                model=model,
                image_path=image_path,
                conf_threshold=conf_threshold,
                imgsz=imgsz,
                use_sahi=use_sahi,
                sahi_config=sahi_config,
                use_objectness=use_objectness,
                obj_threshold=obj_threshold,
                device=device,
            )
            all_predictions.append(preds)
        except Exception as e:
            print(f"[⚠️] Error processing {image_path}: {e}")
            all_predictions.append(np.zeros((0, 6)))

    return all_predictions


def load_test_dataset(
    data_yaml_path: str,
    split: str = "test",
) -> Tuple[List[str], List[np.ndarray], List[np.ndarray]]:
    """Load a YOLO dataset for evaluation.

    Args:
        data_yaml_path: Path to the dataset YAML config
        split: Dataset split ('train', 'val', 'test')

    Returns:
        Tuple of (image_paths, gt_boxes_list, gt_classes_list)
        where gt_boxes_list[i] is [M_i, 4] and gt_classes_list[i] is [M_i]
    """
    import yaml

    with open(data_yaml_path, "r") as f:
        data_cfg = yaml.safe_load(f)

    # Resolve dataset root
    dataset_root = data_cfg.get("path", "")
    if not os.path.isabs(dataset_root):
        dataset_root = os.path.join(os.path.dirname(data_yaml_path), dataset_root)

    # Get image and label directories
    img_dir = os.path.join(dataset_root, data_cfg.get(split, f"images/{split}"))

    # Collect image paths
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    image_paths = sorted(
        [
            os.path.join(img_dir, f)
            for f in os.listdir(img_dir)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]
    )

    # Load ground truth labels
    gt_boxes_list = []
    gt_classes_list = []

    for img_path in image_paths:
        # Construct label path
        lbl_path = img_path.replace("images", "labels")
        lbl_path = os.path.splitext(lbl_path)[0] + ".txt"

        if os.path.exists(lbl_path):
            boxes, classes = _parse_yolo_label(lbl_path, img_path)
            gt_boxes_list.append(boxes)
            gt_classes_list.append(classes)
        else:
            gt_boxes_list.append(np.zeros((0, 4)))
            gt_classes_list.append(np.zeros(0, dtype=int))

    return image_paths, gt_boxes_list, gt_classes_list


def _parse_yolo_label(
    label_path: str,
    image_path: str,
) -> Tuple[np.ndarray, np.ndarray]:
    """Parse a YOLO format label file into boxes and classes.

    YOLO format: class_id x_center y_center width height (normalized)
    For segmentation: class_id x1 y1 x2 y2 x3 y3 ... (normalized polygon)

    Args:
        label_path: Path to the label file
        image_path: Path to the corresponding image (for dimensions)

    Returns:
        Tuple of (boxes [M, 4], classes [M])
    """
    from PIL import Image

    img = Image.open(image_path)
    img_w, img_h = img.size

    boxes = []
    classes = []

    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            cls_id = int(parts[0])

            if len(parts) == 5:
                # Detection format: class x_center y_center width height
                xc, yc, w, h = (
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3]),
                    float(parts[4]),
                )
                x1 = (xc - w / 2) * img_w
                y1 = (yc - h / 2) * img_h
                x2 = (xc + w / 2) * img_w
                y2 = (yc + h / 2) * img_h
            else:
                # Segmentation format: class x1 y1 x2 y2 x3 y3 ...
                # Extract bounding box from polygon
                coords = [float(x) for x in parts[1:]]
                xs = coords[0::2]
                ys = coords[1::2]
                x1 = min(xs) * img_w
                y1 = min(ys) * img_h
                x2 = max(xs) * img_w
                y2 = max(ys) * img_h

            boxes.append([x1, y1, x2, y2])
            classes.append(cls_id)

    if not boxes:
        return np.zeros((0, 4)), np.zeros(0, dtype=int)

    return np.array(boxes), np.array(classes, dtype=int)
