import os
import pytest
import yaml
from pathlib import Path


def load_dataset_config():
    """Helper fixture to parse active dataset boundaries."""
    config_path = Path("data/processed/yolo_seg/data.yaml")
    if not config_path.exists():
        pytest.skip("data.yaml not generated yet. Run 'make data-consolidate' first.")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def test_processed_directory_scaffolding():
    """Verifies that splits contain matching image and label directories."""
    data_cfg = load_dataset_config()
    dataset_root = Path(data_cfg["path"])

    for split in ["train", "val", "test"]:
        assert (
            dataset_root / split / "images"
        ).exists(), f"Missing {split} image directory"
        assert (
            dataset_root / split / "labels"
        ).exists(), f"Missing {split} label directory"


def test_label_synchronization_and_bounds():
    """Ensures every image has a matching label and all polygon masks are normalized."""
    data_cfg = load_dataset_config()
    dataset_root = Path(data_cfg["path"])

    for split in ["train", "val"]:
        img_dir = dataset_root / split / "images"
        lbl_dir = dataset_root / split / "labels"

        images = [
            f for f in os.listdir(img_dir) if f.endswith((".jpg", ".png", ".jpeg"))
        ]

        for img_file in images:
            base_name = os.path.splitext(img_file)[0]
            lbl_file = f"{base_name}.txt"
            lbl_path = lbl_dir / lbl_file

            # 1. Structural Lineage Check
            assert (
                lbl_path.exists()
            ), f"Data Link Broken: Image {img_file} has no matching label file."

            # 2. Coordinate Boundaries Validation
            with open(lbl_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    tokens = line.strip().split()
                    if not tokens:
                        continue
                    # Token index 0 is class id, index 1+ are alternating x, y polygon vertices
                    coordinates = [float(x) for x in tokens[1:]]

                    for coord in coordinates:
                        assert (
                            0.0 <= coord <= 1.0
                        ), f"Quantization Bound Violation: Coordinate {coord} in {lbl_file} is out of bounds!"
