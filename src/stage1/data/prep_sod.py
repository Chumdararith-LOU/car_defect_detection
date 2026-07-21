import shutil
import cv2
from pathlib import Path
import yaml


def verify_and_copy_sod(raw_sod_dir, processed_sod_dir):
    raw_dir = Path(raw_sod_dir)
    out_dir = Path(processed_sod_dir)

    splits = {
        "train": (raw_dir / "CarDD-TR" / "train_pair.lst", raw_dir / "CarDD-TR"),
        "val": (raw_dir / "CarDD-VAL" / "val.lst", raw_dir / "CarDD-VAL"),
        "test": (raw_dir / "CarDD-TE" / "test.lst", raw_dir / "CarDD-TE"),
    }

    # Build fresh output directories
    if out_dir.exists():
        shutil.rmtree(out_dir)

    total_valid = 0

    for split_name, (lst_path, split_base_dir) in splits.items():
        if not lst_path.exists():
            print(f"[!] Warning: Missing {lst_path.name}. Skipping {split_name}.")
            continue

        print(f"\n[+] Processing {split_name.upper()} split...")
        img_out_dir = out_dir / split_name / "images"
        mask_out_dir = out_dir / split_name / "masks"
        img_out_dir.mkdir(parents=True, exist_ok=True)
        mask_out_dir.mkdir(parents=True, exist_ok=True)

        valid_count = 0

        with open(lst_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue

            if len(parts) >= 2:
                img_rel_path, mask_rel_path = parts[0], parts[1]
            else:
                img_filename = parts[0]
                stem = Path(img_filename).stem
                prefix = split_base_dir.name

                img_rel_path = f"{prefix}-Image/{stem}.jpg"
                mask_rel_path = f"{prefix}-Mask/{stem}.png"

            img_src = split_base_dir / img_rel_path
            mask_src = split_base_dir / mask_rel_path

            if not img_src.exists() or not mask_src.exists():
                print(f"    [-] Missing file pair for {img_rel_path}, skipping.")
                continue

            img = cv2.imread(str(img_src))
            mask = cv2.imread(str(mask_src), cv2.IMREAD_GRAYSCALE)

            if img is None or mask is None:
                print(f"    [-] Corrupted file detected, skipping: {img_src.name}")
                continue

            shutil.copy(img_src, img_out_dir / img_src.name)
            mask[mask > 0] = 1
            cv2.imwrite(str(mask_out_dir / mask_src.name), mask)
            valid_count += 1
            total_valid += 1

        print(f"    -> Successfully verified and copied {valid_count} pairs.")

    yaml_data = {
        "path": str(out_dir.absolute()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "masks_dir": "masks",
        "names": {0: "background", 1: "anomaly"},
    }

    yaml_path = out_dir / "sod_data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    print(f"    [+] Auto-generated semantic dataset descriptor at: {yaml_path}")

    print(f"\n[✓] SOD Dataset preparation complete. Total clean pairs: {total_valid}")


if __name__ == "__main__":
    RAW_SOD = "data/raw/CarDD_release/CarDD_SOD"
    PROCESSED_SOD = "data/processed/sod"
    print("=====================================================")
    print("   INITIALIZING SOD DATASET PREPARATION")
    print("=====================================================")
    verify_and_copy_sod(RAW_SOD, PROCESSED_SOD)
