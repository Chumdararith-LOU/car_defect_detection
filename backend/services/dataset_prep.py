"""Dataset preparation service: whole-dataset ZIP import + split-structure detection.

Supported physical layouts (auto-detected):
  ultralytics : images/<split>/ + labels/<split>/   (split in train/val/test)
  grouped     : <split>/images/ + <split>/labels/
  unsplit     : images/ + labels/                    (single pool, no splits)
  flat        : image + label files loose in the root
"""

import io
import logging
import random
import shutil
import zipfile
from pathlib import Path

import yaml

from schemas.dataset_prep import (
    DetectedSplit,
    ImportDatasetResponse,
    SplitLayout,
    SplitStructure,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
LABEL_EXTENSIONS = {".txt"}
MASK_EXTENSIONS = IMAGE_EXTENSIONS
SPLIT_NAMES = ("train", "val", "test")


def _find_dataset_root(dataset_id: str) -> Path | None:
    """Find the actual root path for a dataset ID by scanning data/processed/.
    Handles nested structures like stage3/car_damages_panel/."""
    for yaml_file in DATA_PROCESSED_DIR.rglob("*.yaml"):
        if "archive" in str(yaml_file):
            continue
        if any(part.startswith(".") for part in yaml_file.parts):
            continue

        # Generate ID using same logic as dataset_registry.py
        try:
            rel = yaml_file.relative_to(DATA_PROCESSED_DIR)
            if yaml_file.name in ("data.yaml", "dataset.yaml"):
                parent_str = str(rel.parent)
                if parent_str == ".":
                    gen_id = yaml_file.stem
                else:
                    gen_id = parent_str.replace("/", "_").replace("\\", "_")
            else:
                gen_id = str(rel.with_suffix("")).replace("/", "_").replace("\\", "_")
        except ValueError:
            gen_id = yaml_file.stem

        if gen_id == dataset_id:
            # Resolve the actual root path
            with open(yaml_file, "r") as f:
                import yaml

                yaml_data = yaml.safe_load(f)
            if yaml_data and "path" in yaml_data:
                root = Path(yaml_data["path"])
                # Relative paths resolve against the YAML file's directory (Ultralytics convention)
                if not root.is_absolute():
                    candidate = (yaml_file.parent / root).resolve()
                    if candidate.exists():
                        return candidate
                if root.exists():
                    return root.resolve()
            # Fallback: YAML file's parent
            return yaml_file.parent

    return None


def _count_files(directory: Path, extensions: set[str]) -> int:
    if not directory.exists() or not directory.is_dir():
        return 0
    return sum(
        1 for f in directory.iterdir() if f.is_file() and f.suffix.lower() in extensions
    )


def _find_data_yaml(root: Path) -> Path | None:
    for cand in ("data.yaml", "dataset.yaml"):
        if (root / cand).exists():
            return root / cand
    root_yamls = sorted(root.glob("*.yaml"))
    if root_yamls:
        return root_yamls[0]
    for p in sorted(root.rglob("*.yaml")):
        return p
    return None


def _finalize(
    dataset_id: str,
    layout: SplitLayout,
    data_yaml: Path | None,
    splits: list[DetectedSplit],
    warnings: list[str],
) -> SplitStructure:
    total_images = sum(s.image_count for s in splits)
    total_labels = sum(s.label_count for s in splits)
    names = {s.name for s in splits}
    is_split = bool(names & {"train", "val"})
    for s in splits:
        if s.image_count > 0 and s.label_count == 0:
            warnings.append(f"Split '{s.name}': {s.image_count} images but 0 labels.")
        elif s.label_count > s.image_count:
            warnings.append(
                f"Split '{s.name}': more labels ({s.label_count}) than images ({s.image_count})."
            )
    return SplitStructure(
        dataset_id=dataset_id,
        layout=layout,
        has_data_yaml=data_yaml is not None,
        splits=splits,
        total_images=total_images,
        total_labels=total_labels,
        is_split=is_split,
        has_test="test" in names,
        warnings=warnings,
    )


def _find_annotation_dir(img_dir: Path, kind: str) -> Path | None:
    """Derive an annotation dir by replacing the 'images' path component.
    root/images/train -> root/labels/train  (kind='labels')
    root/train/images -> root/train/masks   (kind='masks')"""
    parts = list(img_dir.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            parts[i] = kind
            return Path(*parts)
    return None


def _find_annotation_for_image(img_path: Path) -> tuple[Path | None, str]:
    """Find the annotation file for an image.
    Returns (path, kind) where kind is 'labels' (YOLO txt) or 'masks' (semantic)."""
    # Try YOLO .txt label first
    lbl_candidate = _find_annotation_dir(img_path, "labels")
    if lbl_candidate is not None:
        txt_path = lbl_candidate.with_suffix(".txt")
        if txt_path.exists():
            return txt_path, "labels"
    # Try semantic mask (any image extension)
    mask_candidate = _find_annotation_dir(img_path, "masks")
    if mask_candidate is not None:
        for ext in sorted(IMAGE_EXTENSIONS):
            mask_path = mask_candidate.with_suffix(ext)
            if mask_path.exists():
                return mask_path, "masks"
    return None, ""


def _count_annotations(img_dir: Path) -> tuple[int, str | None, str | None]:
    """Count annotations for an image dir. Prefers YOLO .txt labels, then
    falls back to semantic masks. Returns (count, path, format)."""
    lbl_dir = _find_annotation_dir(img_dir, "labels")
    if lbl_dir is not None and lbl_dir.is_dir():
        n = _count_files(lbl_dir, LABEL_EXTENSIONS)
        if n > 0:
            return n, str(lbl_dir), "yolo_txt"
    mask_dir = _find_annotation_dir(img_dir, "masks")
    if mask_dir is not None and mask_dir.is_dir():
        n = _count_files(mask_dir, MASK_EXTENSIONS)
        if n > 0:
            return n, str(mask_dir), "semantic_mask"
    if lbl_dir is not None and lbl_dir.is_dir():
        return 0, str(lbl_dir), "yolo_txt"
    if mask_dir is not None and mask_dir.is_dir():
        return 0, str(mask_dir), "semantic_mask"
    return 0, None, None


def _detect(root: Path, dataset_id: str) -> SplitStructure:
    warnings: list[str] = []
    data_yaml = _find_data_yaml(root)
    splits: list[DetectedSplit] = []

    def add_split(name: str, img_dir: Path) -> None:
        count, ann_path, ann_format = _count_annotations(img_dir)
        splits.append(
            DetectedSplit(
                name=name,
                image_count=_count_files(img_dir, IMAGE_EXTENSIONS),
                label_count=count,
                images_path=str(img_dir),
                labels_path=ann_path,
                label_format=ann_format,
            )
        )

    images_root = root / "images"

    # ultralytics: images/<split> + (labels/<split> OR masks/<split>)
    if images_root.is_dir():
        for split in SPLIT_NAMES:
            img_dir = images_root / split
            if img_dir.is_dir():
                add_split(split, img_dir)
        if splits:
            return _finalize(
                dataset_id, SplitLayout.ULTRALYTICS, data_yaml, splits, warnings
            )
        # images/ with no split subdirs -> unsplit pool
        add_split("all", images_root)
        return _finalize(dataset_id, SplitLayout.UNSPLIT, data_yaml, splits, warnings)

    # grouped: <split>/images + (<split>/labels OR <split>/masks)
    for split in SPLIT_NAMES:
        grp_img = root / split / "images"
        if grp_img.is_dir():
            add_split(split, grp_img)
    if splits:
        return _finalize(dataset_id, SplitLayout.GROUPED, data_yaml, splits, warnings)

    # flat: loose files in root
    img_count = _count_files(root, IMAGE_EXTENSIONS)
    if img_count > 0:
        txt_count = _count_files(root, LABEL_EXTENSIONS)
        splits.append(
            DetectedSplit(
                name="all",
                image_count=img_count,
                label_count=txt_count,
                images_path=str(root),
                labels_path=str(root) if txt_count > 0 else None,
                label_format="yolo_txt" if txt_count > 0 else None,
            )
        )
        return _finalize(dataset_id, SplitLayout.FLAT, data_yaml, splits, warnings)

    warnings.append("No images detected in dataset.")
    return _finalize(dataset_id, SplitLayout.UNKNOWN, data_yaml, [], warnings)


def _maybe_unwrap_single_folder(root: Path) -> None:
    """If extraction produced exactly one wrapper folder, lift its contents up.
    Filters out macOS metadata folders like __MACOSX."""
    entries = [
        e for e in root.iterdir() if not e.name.startswith(".") and e.name != "__MACOSX"
    ]
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for item in inner.iterdir():
            shutil.move(str(item), str(root / item.name))
        inner.rmdir()
    # Also clean up __MACOSX if it exists
    macosx_dir = root / "__MACOSX"
    if macosx_dir.exists():
        shutil.rmtree(macosx_dir)


def import_dataset_zip(version_name: str, zip_bytes: bytes) -> ImportDatasetResponse:
    """Extract a whole YOLO-format dataset ZIP into data/processed/{version_name}
    and auto-detect its split structure."""
    out_dir = DATA_PROCESSED_DIR / version_name
    if out_dir.exists():
        raise ValueError(f"Dataset '{version_name}' already exists at {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for name in zf.namelist():
                if name.startswith("/") or ".." in name:
                    raise ValueError(f"Unsafe path in ZIP: {name}")
            zf.extractall(out_dir)
    except Exception:
        shutil.rmtree(out_dir, ignore_errors=True)
        raise

    _maybe_unwrap_single_folder(out_dir)
    structure = _detect(out_dir, version_name)
    return ImportDatasetResponse(
        success=True,
        dataset_id=version_name,
        path=str(out_dir),
        structure=structure,
        message=(
            f"Imported '{version_name}' ({structure.total_images} images). "
            f"Layout: {structure.layout.value}; "
            f"{'already split' if structure.is_split else 'not split yet'}."
        ),
    )


def detect_dataset_structure(dataset_id: str) -> SplitStructure:
    """Detect split structure of an existing dataset under data/processed/."""
    root = _find_dataset_root(dataset_id)
    if root is None or not root.exists():
        raise ValueError(f"Dataset '{dataset_id}' not found")
    return _detect(root, dataset_id)


def resplit_dataset(
    dataset_id: str,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> SplitStructure:
    """Re-split a dataset into train/val/test using image-level split.
    Handles both YOLO .txt labels and semantic segmentation masks."""
    root = _find_dataset_root(dataset_id)
    if root is None or not root.exists():
        raise ValueError(f"Dataset '{dataset_id}' not found")

    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-5:
        raise ValueError("Ratios must sum to 1.0")

    # 1. Find existing yaml to preserve class names + write back in place
    data_yaml = _find_data_yaml(root)
    yaml_data = {}
    if data_yaml:
        try:
            with open(data_yaml, "r") as f:
                yaml_data = yaml.safe_load(f) or {}
        except Exception:
            pass

    # 2. Gather (image, annotation, kind) tuples
    pairs: list[tuple[Path, Path, str]] = []
    for img_path in root.rglob("*"):
        if not img_path.is_file() or img_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        # Skip temp leftovers and mask files (masks are images too)
        if "_temp_resplit" in img_path.parts or "masks" in img_path.parts:
            continue
        ann_path, ann_kind = _find_annotation_for_image(img_path)
        if ann_path is not None:
            pairs.append((img_path, ann_path, ann_kind))

    if not pairs:
        raise ValueError(f"No valid image/annotation pairs found in '{dataset_id}'")

    has_masks = any(kind == "masks" for _, _, kind in pairs)

    random.seed(seed)
    random.shuffle(pairs)
    total = len(pairs)
    train_n = int(round(total * train_ratio))
    val_n = int(round(total * val_ratio))
    test_n = total - train_n - val_n
    if test_ratio <= 1e-9:
        val_n += test_n
        test_n = 0
    if total >= 2:
        if val_ratio > 1e-9 and val_n == 0:
            val_n = 1
            train_n -= 1
        if test_ratio > 1e-9 and test_n == 0:
            test_n = 1
            if val_n > 1:
                val_n -= 1
            else:
                train_n -= 1
    if train_n < 0:
        train_n = 0
    train_end = train_n
    val_end = train_n + val_n
    splits_map = {
        "train": pairs[:train_end],
        "val": pairs[train_end:val_end],
        "test": pairs[val_end:],
    }

    temp_dir = root / "_temp_resplit"
    temp_dir.mkdir(exist_ok=True)

    for split_name, items in splits_map.items():
        for img_path, ann_path, _ in items:
            shutil.move(str(img_path), str(temp_dir / f"{split_name}_{img_path.name}"))
            shutil.move(str(ann_path), str(temp_dir / f"{split_name}_{ann_path.name}"))

    for split, count in (("train", train_n), ("val", val_n), ("test", test_n)):
        if count <= 0:
            continue
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)
        if has_masks:
            (root / "masks" / split).mkdir(parents=True, exist_ok=True)

    for split_name, items in splits_map.items():
        target_img_dir = root / "images" / split_name
        for img_path, ann_path, ann_kind in items:
            ann_subdir = "masks" if ann_kind == "masks" else "labels"
            target_ann_dir = root / ann_subdir / split_name
            shutil.move(
                str(temp_dir / f"{split_name}_{img_path.name}"),
                str(target_img_dir / img_path.name),
            )
            shutil.move(
                str(temp_dir / f"{split_name}_{ann_path.name}"),
                str(target_ann_dir / ann_path.name),
            )

    # Cleanup empty source dirs
    for split in ("train", "val", "test"):
        for subdir in ("images", "labels", "masks"):
            d = root / subdir / split
            if d.exists() and not any(d.iterdir()):
                try:
                    d.rmdir()
                except OSError:
                    pass
    if temp_dir.exists() and not any(temp_dir.iterdir()):
        try:
            temp_dir.rmdir()
        except OSError:
            pass

    # 5. Write yaml back IN PLACE (avoids duplicate yaml files in registry)
    names = yaml_data.get("names", {})
    nc = yaml_data.get("nc", len(names) if isinstance(names, dict) else 0)

    yaml_content = {
        "path": str(root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "nc": nc,
        "names": names,
    }
    if test_n > 0:
        yaml_content["test"] = "images/test"
    if has_masks:
        yaml_content["masks_dir"] = "masks"

    target_yaml = data_yaml if data_yaml is not None else (root / "data.yaml")
    with open(target_yaml, "w") as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)

    # 6. Re-detect and return new structure
    return _detect(root, dataset_id)
