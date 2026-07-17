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

    sizes = []
    for p in all_masks:
        m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if m is None:
            continue
        active = np.sum(m > 0)
        if active > 0:
            sizes.append((p, active))

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

        orig_fraction = orig_pixels / (h * w)

        resized = cv2.resize(mask_bin, target_size, interpolation=cv2.INTER_AREA)
        surviving_fraction = np.sum(resized >= threshold) / (
            target_size[0] * target_size[1]
        )

        preserved_pct = (
            (surviving_fraction / orig_fraction * 100) if orig_fraction > 0 else 0
        )
        rates.append(preserved_pct)
        print(
            f"  {p.name}: {orig_pixels}px ({orig_fraction*100:.3f}% of canvas) -> {preserved_pct:.1f}% preserved"
        )

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
    import argparse

    parser = argparse.ArgumentParser(
        description="Downscale Diagnostic: Analyze spatial area fraction preservation of micro-defects"
    )
    parser.add_argument(
        "--mask_dir",
        type=str,
        default="data/processed/sod/val/masks",
        help="Directory containing ground truth png masks",
    )
    parser.add_argument(
        "--target_w", type=int, default=320, help="Target simulation width resolution"
    )
    parser.add_argument(
        "--target_h", type=int, default=320, help="Target simulation height resolution"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Binarization confidence threshold after resizing",
    )
    parser.add_argument(
        "--percentile",
        type=int,
        default=10,
        help="Focus on the bottom X% smallest defects",
    )
    parser.add_argument(
        "--samples", type=int, default=100, help="Limit execution sample size"
    )
    args = parser.parse_args()

    if Path(args.mask_dir).exists():
        diagnostic_downscale_survival_v2(
            mask_dir=args.mask_dir,
            target_size=(args.target_w, args.target_h),
            threshold=args.threshold,
            sample_percentile=args.percentile,
            n_samples=args.samples,
        )
    else:
        print(f"[!] Please ensure the dataset exists at: {args.mask_dir}")
