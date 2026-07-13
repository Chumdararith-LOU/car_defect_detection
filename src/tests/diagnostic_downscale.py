import cv2
import numpy as np
from pathlib import Path


def diagnostic_downscale_survival_v2(
    mask_dir,
    target_size=(320, 320),
    threshold=0.70,
    sample_percentile=10,
    n_samples=100,
):
    """
    Evaluates spatial feature loss by comparing proportional area fractions
    before and after downscaling, specifically targeting the dataset's smallest defects.
    """
    mask_path_obj = Path(mask_dir)
    all_masks = list(mask_path_obj.glob("*.png"))

    if not all_masks:
        print(f"[!] No masks found in {mask_dir}.")
        return

    print("[+] Scanning dataset to isolate the smallest defects...")

    # 1. Measure every defect's size first
    sizes = []
    for p in all_masks:
        m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if m is None:
            continue
        # Convert YOLO class ID / 255 scaled masks to binary [0, 1]
        active = np.sum(m > 0)
        if active > 0:
            sizes.append((p, active))

    # 2. Target the smallest defects in the dataset (the actual risk zone)
    sizes.sort(key=lambda x: x[1])
    cutoff = max(1, int(len(sizes) * sample_percentile / 100))
    sample = sizes[:cutoff][:n_samples]

    print("\n" + "=" * 70)
    print(f" 🔬 DOWNSCALE DIAGNOSTIC V2: TARGETING BOTTOM {sample_percentile}% DEFECTS")
    print("=" * 70)
    print(f"Testing {len(sample)} of the dataset's genuinely smallest defects\n")

    rates = []
    for p, orig_pixels in sample:
        m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        h, w = m.shape
        mask_bin = (m > 0).astype(np.float32)

        # Original proportional footprint
        orig_fraction = orig_pixels / (h * w)

        # Simulate bottleneck and apply threshold
        resized = cv2.resize(mask_bin, target_size, interpolation=cv2.INTER_AREA)
        surviving_fraction = np.sum(resized >= threshold) / (
            target_size[0] * target_size[1]
        )

        # Compare fraction-to-fraction, not count-to-count
        preserved_pct = (
            (surviving_fraction / orig_fraction * 100) if orig_fraction > 0 else 0
        )
        rates.append(preserved_pct)
        print(
            f"  {p.name}: {orig_pixels}px ({orig_fraction*100:.3f}% of canvas) -> {preserved_pct:.1f}% preserved"
        )

    # 3. Aggregate Results
    rates = np.array(rates)
    print("-" * 70)
    print(f"Median preservation: {np.median(rates):.1f}%")
    print(f"Worst case (min):    {np.min(rates):.1f}%")
    print(f"10th percentile:     {np.percentile(rates, 10):.1f}%")
    print("=" * 70 + "\n")

    if np.median(rates) < 50.0:
        print(
            "[!] CONCLUSION: The bottleneck mathematically destroys thin/small features."
        )
        print("[!] ACTION: Coarse tiling (1024x1024) is strictly required.")
    else:
        print("[✓] CONCLUSION: Downscaling is safe for this dataset.")


if __name__ == "__main__":
    # Point this to your processed masks directory
    # Depending on your current architecture, it might be in 'masks' or 'labels'
    target_directory = "data/processed/sod/train/masks"

    if Path(target_directory).exists():
        diagnostic_downscale_survival_v2(target_directory)
    else:
        print(f"[!] Please ensure the dataset exists at: {target_directory}")
