"""Service for browsing dataset images and parsing YOLO labels.

Handles:
- Listing images with pagination
- Resolving image/label file paths
- Parsing YOLO label files into structured annotations
"""

import logging
from pathlib import Path
from typing import Optional
import cv2

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def _find_dataset_root(dataset_id: str) -> Optional[Path]:
    """Resolve the root directory for a dataset by its ID."""
    from services.dataset_registry import get_dataset_detail

    detail = get_dataset_detail(dataset_id)
    if detail is None:
        return None
    return Path(detail.root_path)


def _find_images_dir(root: Path, split: str) -> Optional[Path]:
    """Find the images directory for a given split (handles multiple layouts)."""
    candidates = [
        root / "images" / split,  # layout: images/train/
        root / split / "images",  # layout: train/images/
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _find_labels_dir(root: Path, split: str) -> Optional[Path]:
    """Find the labels directory for a given split."""
    candidates = [
        root / "labels" / split,  # layout: labels/train/
        root / split / "labels",  # layout: train/labels/
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _find_masks_dir(root: Path, split: str) -> Optional[Path]:
    """Find the masks directory for semantic segmentation datasets (Stage 1)."""
    candidates = [
        root / "masks" / split,
        root / "masks",  # Sometimes masks are not split by train/val
        root / split / "masks",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def get_mask_path(
    dataset_id: str, filename: str, split: str = "train"
) -> Optional[Path]:
    """Get the absolute path to a semantic mask image (Stage 1)."""
    root = _find_dataset_root(dataset_id)
    if root is None:
        return None

    masks_dir = _find_masks_dir(root, split)
    if masks_dir is None:
        return None

    # Try common image extensions
    stem = Path(filename).stem
    for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
        mask_path = masks_dir / f"{stem}{ext}"
        if mask_path.exists():
            return mask_path
    return None


def list_dataset_images(
    dataset_id: str,
    page: int = 1,
    page_size: int = 20,
    split: str = "train",
) -> dict:
    """List image filenames in a dataset with pagination."""
    root = _find_dataset_root(dataset_id)
    if root is None:
        return {
            "images": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    images_dir = _find_images_dir(root, split)
    if images_dir is None:
        return {
            "images": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    all_images = sorted(
        f.name
        for f in images_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )

    total = len(all_images)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "images": all_images[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_image_path(
    dataset_id: str, filename: str, split: str = "train"
) -> Optional[Path]:
    """Get the absolute path to a specific image file."""
    root = _find_dataset_root(dataset_id)
    if root is None:
        return None

    images_dir = _find_images_dir(root, split)
    if images_dir is None:
        return None

    image_path = images_dir / filename
    if image_path.exists():
        return image_path
    return None


def get_label_path(
    dataset_id: str, filename: str, split: str = "train"
) -> Optional[Path]:
    """Get the absolute path to the YOLO label file for an image."""
    root = _find_dataset_root(dataset_id)
    if root is None:
        return None

    labels_dir = _find_labels_dir(root, split)
    if labels_dir is None:
        return None

    label_name = Path(filename).stem + ".txt"
    label_path = labels_dir / label_name
    if label_path.exists():
        return label_path
    return None


def parse_yolo_labels(
    dataset_id: str, filename: str, split: str = "train"
) -> list[dict]:
    """Parse YOLO labels (instance seg) or semantic masks (Stage 1) into annotations."""
    class_names = _get_class_names(dataset_id)

    # 1. Try YOLO instance segmentation (.txt)
    label_path = get_label_path(dataset_id, filename, split)
    if label_path is not None:
        return _parse_txt_labels(label_path, class_names)

    # 2. Fallback: Semantic segmentation mask (image file)
    mask_path = get_mask_path(dataset_id, filename, split)
    if mask_path is not None:
        return _parse_semantic_mask(mask_path, class_names)

    return []


def _parse_txt_labels(label_path: Path, class_names: list[str]) -> list[dict]:
    """Parse standard YOLO instance segmentation .txt files."""
    annotations = []
    try:
        with open(label_path, "r") as f:
            for line_idx, line in enumerate(f):
                parts = line.strip().split()
                if len(parts) < 7:  # Need at least class_id + 3 points
                    continue

                class_id = int(parts[0])
                coords = [float(v) for v in parts[1:]]

                polygon = []
                for i in range(0, len(coords) - 1, 2):
                    polygon.append([coords[i], coords[i + 1]])

                annotations.append(
                    {
                        "index": line_idx,
                        "class_id": class_id,
                        "class_name": (
                            class_names[class_id]
                            if class_id < len(class_names)
                            else f"class_{class_id}"
                        ),
                        "polygon": polygon,
                    }
                )
    except Exception as e:
        logger.warning("Failed to parse label file %s: %s", label_path, e)
    return annotations


def _parse_semantic_mask(mask_path: Path, class_names: list[str]) -> list[dict]:
    """Extract polygons from a semantic segmentation mask image (Stage 1)."""
    try:
        img = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return []

        h, w = img.shape
        # Threshold to binary (any non-zero pixel is a defect)
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)

        # Find external contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        annotations = []
        for idx, contour in enumerate(contours):
            # Simplify contour to prevent SVG lag from thousands of points
            epsilon = 0.005 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) < 3:
                continue

            # Normalize coordinates to 0-1
            polygon = []
            for pt in approx:
                x = pt[0][0] / w
                y = pt[0][1] / h
                polygon.append([x, y])

            annotations.append(
                {
                    "index": idx,
                    "class_id": 1,  # Stage 1 YAML defines 1 as 'defect'
                    "class_name": class_names[1] if len(class_names) > 1 else "defect",
                    "polygon": polygon,
                }
            )
        return annotations
    except Exception as e:
        logger.warning("Failed to parse semantic mask %s: %s", mask_path, e)
        return []


def _get_class_names(dataset_id: str) -> list[str]:
    """Get class names for a dataset from the registry."""
    from services.dataset_registry import get_dataset_detail

    detail = get_dataset_detail(dataset_id)
    if detail is None:
        return []
    return detail.class_names
