"""Dataset preparation service: whole-dataset ZIP import + split-structure detection.

Supported physical layouts (auto-detected):
  ultralytics : images/<split>/ + labels/<split>/   (split in train/val/test)
  grouped     : <split>/images/ + <split>/labels/
  unsplit     : images/ + labels/                    (single pool, no splits)
  flat        : image + label files loose in the root
"""

import io
import logging
import shutil
import zipfile
from pathlib import Path

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
SPLIT_NAMES = ("train", "val", "test")


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
    for p in root.rglob("*.yaml"):
        if p.name in ("data.yaml", "dataset.yaml"):
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


def _detect(root: Path, dataset_id: str) -> SplitStructure:
    warnings: list[str] = []
    data_yaml = _find_data_yaml(root)
    splits: list[DetectedSplit] = []

    images_root = root / "images"
    labels_root = root / "labels"

    # ultralytics: images/<split> + labels/<split>
    if images_root.is_dir():
        for split in SPLIT_NAMES:
            img_dir = images_root / split
            if img_dir.is_dir():
                lbl_dir = labels_root / split
                splits.append(
                    DetectedSplit(
                        name=split,
                        image_count=_count_files(img_dir, IMAGE_EXTENSIONS),
                        label_count=_count_files(lbl_dir, LABEL_EXTENSIONS),
                        images_path=str(img_dir),
                        labels_path=str(lbl_dir) if lbl_dir.is_dir() else None,
                    )
                )
        if splits:
            return _finalize(
                dataset_id, SplitLayout.ULTRALYTICS, data_yaml, splits, warnings
            )

        # images/ with no split subdirs -> unsplit pool
        splits.append(
            DetectedSplit(
                name="all",
                image_count=_count_files(images_root, IMAGE_EXTENSIONS),
                label_count=_count_files(labels_root, LABEL_EXTENSIONS),
                images_path=str(images_root),
                labels_path=str(labels_root) if labels_root.is_dir() else None,
            )
        )
        return _finalize(dataset_id, SplitLayout.UNSPLIT, data_yaml, splits, warnings)

    # grouped: <split>/images + <split>/labels
    for split in SPLIT_NAMES:
        grp = root / split
        if (grp / "images").is_dir():
            splits.append(
                DetectedSplit(
                    name=split,
                    image_count=_count_files(grp / "images", IMAGE_EXTENSIONS),
                    label_count=_count_files(grp / "labels", LABEL_EXTENSIONS),
                    images_path=str(grp / "images"),
                    labels_path=(
                        str(grp / "labels") if (grp / "labels").is_dir() else None
                    ),
                )
            )
    if splits:
        return _finalize(dataset_id, SplitLayout.GROUPED, data_yaml, splits, warnings)

    # flat: loose files in root
    img_count = _count_files(root, IMAGE_EXTENSIONS)
    if img_count > 0:
        splits.append(
            DetectedSplit(
                name="all",
                image_count=img_count,
                label_count=_count_files(root, LABEL_EXTENSIONS),
                images_path=str(root),
                labels_path=str(root),
            )
        )
        return _finalize(dataset_id, SplitLayout.FLAT, data_yaml, splits, warnings)

    warnings.append("No images detected in dataset.")
    return _finalize(dataset_id, SplitLayout.UNKNOWN, data_yaml, [], warnings)


def _maybe_unwrap_single_folder(root: Path) -> None:
    """If extraction produced exactly one wrapper folder, lift its contents up."""
    entries = [e for e in root.iterdir() if not e.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for item in inner.iterdir():
            shutil.move(str(item), str(root / item.name))
        inner.rmdir()


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
    root = DATA_PROCESSED_DIR / dataset_id
    if not root.exists():
        raise ValueError(f"Dataset '{dataset_id}' not found at {root}")
    return _detect(root, dataset_id)
