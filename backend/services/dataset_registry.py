"""Dataset discovery and registry service for Phase 9.

Scans data/processed/ for Ultralytics dataset YAML files, parses metadata,
counts images per split, and computes class distributions on demand.
"""

import logging
from pathlib import Path
from typing import Optional

import yaml

from schemas.dataset import (
    ClassDistributionItem,
    DatasetDetail,
    DatasetStage,
    DatasetStatus,
    DatasetSummary,
    FilenameOverlap,
    LeakageAuditResult,
    SplitInfo,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# Champion dataset identifiers (from champion_manifest.md)
# ---------------------------------------------------------------------------

CHAMPION_DATASETS: dict[DatasetStage, str] = {
    DatasetStage.STAGE1: "sod_tiled",
    DatasetStage.STAGE2: "yolo_seg_clean_2200_7cls",
    DatasetStage.STAGE3: "car_damages_panel",
}

# ---------------------------------------------------------------------------
# Stage inference keywords
# ---------------------------------------------------------------------------

STAGE_KEYWORDS: dict[DatasetStage, list[str]] = {
    DatasetStage.STAGE1: ["sod", "binary", "anomaly"],
    DatasetStage.STAGE3: ["stage3", "panel", "car_damages_panel"],
    DatasetStage.STAGE2: ["stage2", "7cls", "defect", "6k", "clean_data"],
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_dataset_yamls() -> list[Path]:
    """Recursively find all dataset YAML files in data/processed/."""
    yamls: list[Path] = []
    if not DATA_PROCESSED_DIR.exists():
        logger.warning("Dataset directory not found: %s", DATA_PROCESSED_DIR)
        return yamls

    for yaml_file in DATA_PROCESSED_DIR.rglob("*.yaml"):
        # Skip archives and hidden dirs
        if "archive" in str(yaml_file):
            continue
        if any(part.startswith(".") for part in yaml_file.parts):
            continue
        yamls.append(yaml_file)

    return sorted(yamls)


def _parse_dataset_yaml(yaml_path: Path) -> Optional[dict]:
    """Parse a dataset YAML file and return its contents."""
    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:
        logger.warning("Failed to parse %s: %s", yaml_path, e)
        return None


def _resolve_root_path(yaml_path: Path, yaml_data: dict) -> Path:
    """Resolve the dataset root path with fallback for portability."""
    path_str = yaml_data.get("path", "")
    if not path_str:
        return yaml_path.parent

    root = Path(path_str)
    if root.exists():
        return root

    # Fallback: YAML file's parent directory (handles moved repos)
    fallback = yaml_path.parent
    if fallback.exists():
        return fallback

    return root


def _infer_stage(yaml_path: Path, yaml_data: dict) -> DatasetStage:
    """Infer which pipeline stage a dataset belongs to."""
    path_str = str(yaml_path).lower()
    names = yaml_data.get("names", {})
    nc = yaml_data.get("nc", len(names))

    # Check path keywords (most reliable)
    for stage, keywords in STAGE_KEYWORDS.items():
        for kw in keywords:
            if kw in path_str:
                return stage

    # Fallback: infer from class count and names
    names_str = str(names).lower()
    if nc <= 2 or "background" in names_str:
        return DatasetStage.STAGE1
    if nc == 21 or "panel" in names_str:
        return DatasetStage.STAGE3

    return DatasetStage.STAGE2


def _resolve_split_path(root_path: Path, split_value: str) -> Path:
    """Resolve a split path relative to the dataset root."""
    split_path = Path(split_value)
    if split_path.is_absolute():
        return split_path
    return root_path / split_value


def _count_images(directory: Path) -> int:
    """Count image files in a directory (non-recursive)."""
    if not directory.exists() or not directory.is_dir():
        return 0
    return sum(
        1
        for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )


def _extract_class_names(yaml_data: dict) -> list[str]:
    """Extract ordered class names from YAML data."""
    names = yaml_data.get("names", {})
    if isinstance(names, dict):
        sorted_keys = sorted(
            names.keys(), key=lambda x: int(x) if str(x).isdigit() else 0
        )
        return [str(names[k]) for k in sorted_keys]
    if isinstance(names, list):
        return [str(n) for n in names]
    return []


def _build_splits(root_path: Path, yaml_data: dict) -> list[SplitInfo]:
    """Build split info from YAML data."""
    splits: list[SplitInfo] = []
    for split_name in ("train", "val", "test"):
        split_value = yaml_data.get(split_name)
        if not split_value:
            continue
        split_path = _resolve_split_path(root_path, split_value)
        image_count = _count_images(split_path)
        splits.append(
            SplitInfo(
                name=split_name,
                image_count=image_count,
                path=str(split_path),
            )
        )
    return splits


def _is_champion(yaml_path: Path, stage: DatasetStage) -> bool:
    """Check if this dataset is the known champion for its stage.

    Uses exact parent-directory match to avoid false positives
    (e.g. car_damages_panel_smoke should NOT match car_damages_panel).
    """
    champion_name = CHAMPION_DATASETS.get(stage)
    if not champion_name:
        return False

    # Exclude smoke/test variants
    path_str = str(yaml_path).lower()
    if "smoke" in path_str or "test_only" in path_str:
        return False

    # Check exact parent directory name match
    return yaml_path.parent.name == champion_name


def _generate_dataset_id(yaml_path: Path) -> str:
    """Generate a stable dataset ID from the YAML path."""
    try:
        rel = yaml_path.relative_to(DATA_PROCESSED_DIR)
        # If the yaml is data.yaml or dataset.yaml, just use the parent dir name
        if yaml_path.name in ("data.yaml", "dataset.yaml"):
            parent_str = str(rel.parent)
            if parent_str == ".":
                return yaml_path.stem
            return parent_str.replace("/", "_").replace("\\", "_")
        return str(rel.with_suffix("")).replace("/", "_").replace("\\", "_")
    except ValueError:
        return yaml_path.stem


def _dataset_display_name(yaml_path: Path) -> str:
    """Use parent directory name for display (avoids 'data'/'dataset' collisions)."""
    parent = yaml_path.parent.name
    # If parent is data/processed itself, fall back to stem
    if parent in ("processed", "data"):
        return yaml_path.stem
    return parent


def _compute_class_distribution(
    root_path: Path, yaml_data: dict, class_names: list[str]
) -> list[ClassDistributionItem]:
    """Compute instance counts per class by reading YOLO label files."""
    class_counts: dict[int, int] = {}

    for split_name in ("train", "val", "test"):
        split_value = yaml_data.get(split_name)
        if not split_value:
            continue

        split_path = _resolve_split_path(root_path, split_value)
        # Labels are in a parallel directory: images -> labels
        label_path = Path(str(split_path).replace("images", "labels"))

        if not label_path.exists():
            continue

        for label_file in label_path.glob("*.txt"):
            try:
                with open(label_file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            class_id = int(parts[0])
                            class_counts[class_id] = class_counts.get(class_id, 0) + 1
            except Exception:
                continue

    total_instances = sum(class_counts.values())

    distribution: list[ClassDistributionItem] = []
    for class_id in range(len(class_names)):
        count = class_counts.get(class_id, 0)
        percentage = (count / total_instances * 100) if total_instances > 0 else 0.0
        distribution.append(
            ClassDistributionItem(
                class_id=class_id,
                class_name=(
                    class_names[class_id]
                    if class_id < len(class_names)
                    else f"class_{class_id}"
                ),
                instance_count=count,
                percentage=round(percentage, 2),
            )
        )

    return distribution


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_datasets() -> list[DatasetSummary]:
    """List all discovered datasets with summary metadata."""
    datasets: list[DatasetSummary] = []

    for yaml_path in _find_dataset_yamls():
        yaml_data = _parse_dataset_yaml(yaml_path)
        if not yaml_data:
            continue

        # Must have class names to be a valid dataset
        if "names" not in yaml_data:
            continue

        root_path = _resolve_root_path(yaml_path, yaml_data)
        stage = _infer_stage(yaml_path, yaml_data)
        class_names = _extract_class_names(yaml_data)
        nc = yaml_data.get("nc", len(class_names))
        splits = _build_splits(root_path, yaml_data)
        total_images = sum(s.image_count for s in splits)

        datasets.append(
            DatasetSummary(
                dataset_id=_generate_dataset_id(yaml_path),
                name=_dataset_display_name(yaml_path),
                stage=stage,
                yaml_path=str(yaml_path),
                nc=nc,
                class_names=class_names,
                splits=splits,
                total_images=total_images,
                is_champion=_is_champion(yaml_path, stage),
                status=DatasetStatus.RELEASED,
            )
        )

    return datasets


def get_dataset_detail(dataset_id: str) -> Optional[DatasetDetail]:
    """Get full dataset detail including class distribution."""
    for yaml_path in _find_dataset_yamls():
        if _generate_dataset_id(yaml_path) != dataset_id:
            continue

        yaml_data = _parse_dataset_yaml(yaml_path)
        if not yaml_data:
            return None

        root_path = _resolve_root_path(yaml_path, yaml_data)
        stage = _infer_stage(yaml_path, yaml_data)
        class_names = _extract_class_names(yaml_data)
        nc = yaml_data.get("nc", len(class_names))
        splits = _build_splits(root_path, yaml_data)
        total_images = sum(s.image_count for s in splits)
        class_dist = _compute_class_distribution(root_path, yaml_data, class_names)

        return DatasetDetail(
            dataset_id=dataset_id,
            name=_dataset_display_name(yaml_path),
            stage=stage,
            yaml_path=str(yaml_path),
            root_path=str(root_path),
            nc=nc,
            class_names=class_names,
            splits=splits,
            total_images=total_images,
            is_champion=_is_champion(yaml_path, stage),
            status=DatasetStatus.RELEASED,
            class_distribution=class_dist,
        )

    return None


def run_leakage_audit(dataset_id: str) -> Optional[LeakageAuditResult]:
    """Check for filename overlap between train/val/test splits."""
    for yaml_path in _find_dataset_yamls():
        if _generate_dataset_id(yaml_path) != dataset_id:
            continue

        yaml_data = _parse_dataset_yaml(yaml_path)
        if not yaml_data:
            return None

        root_path = _resolve_root_path(yaml_path, yaml_data)

        # Collect filenames per split
        split_files: dict[str, set[str]] = {}
        for split_name in ("train", "val", "test"):
            split_value = yaml_data.get(split_name)
            if not split_value:
                continue
            split_path = _resolve_split_path(root_path, split_value)
            if split_path.exists():
                split_files[split_name] = {
                    f.name for f in split_path.iterdir() if f.is_file()
                }

        # Find filename overlaps across splits
        all_filenames: dict[str, list[str]] = {}
        for split_name, files in split_files.items():
            for fname in files:
                all_filenames.setdefault(fname, []).append(split_name)

        overlaps = [
            FilenameOverlap(filename=fname, found_in=found_in)
            for fname, found_in in all_filenames.items()
            if len(found_in) > 1
        ]

        total_checked = sum(len(files) for files in split_files.values())
        passed = len(overlaps) == 0
        issues: list[str] = []
        if not passed:
            issues.append(f"{len(overlaps)} filename(s) found in multiple splits")

        return LeakageAuditResult(
            dataset_id=dataset_id,
            passed=passed,
            total_checked=total_checked,
            filename_overlaps=overlaps,
            issues=issues,
        )

    return None
