import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from src.inference.router import get_stitched_probability_map


def inspect_geometric_properties(
    img_path, net, device, pixel_thresh_high, pixel_thresh_low
):
    img = cv2.imread(str(img_path))
    if img is None:
        print(f" [!] Could not load {img_path}")
        return

    # Unified 640-resolution processing
    global_probs = get_stitched_probability_map(
        img, net, device, overlap_frac=0.15, imgsz=640
    )

    mask_high = (global_probs >= pixel_thresh_high).astype(np.uint8)
    mask_low = (global_probs >= pixel_thresh_low).astype(np.uint8)

    # Find continuous components in the pathway mask
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask_low, connectivity=8
    )

    print(f"\nAnalyzing: {Path(img_path).name}")
    print(f" -> Global Peak Softmax: {np.max(global_probs):.5f}")
    print(f" -> Components found at tau_low={pixel_thresh_low}: {num_labels - 1}")

    for i in range(1, num_labels):
        # comp_mask = (labels == i).astype(np.uint8)
        comp_max_prob = np.max(global_probs[labels == i])

        has_seed = np.any(mask_high[labels == i] > 0)

        area = stats[i, cv2.CC_STAT_AREA]
        x, y, w, h_box, _ = stats[i]

        aspect_ratio = (
            max(float(h_box) / w, float(w) / h_box) if (w > 0 and h_box > 0) else 0
        )

        print(f"   [Component #{i}]")
        print(f"     * Area (pixels): {area}")
        print(f"     * Peak Softmax:  {comp_max_prob:.5f}")
        print(f"     * Has Seed?      {has_seed} (Requires >= {pixel_thresh_high})")
        print(f"     * Aspect Ratio:  {aspect_ratio:.3f}")


def run_inspection():
    model_weight = "runs/semantic/runs/semantic/Automated_Car_Defect_Stage1_SOD/Stage1_SOD_FocalLoss_Full/weights/best.pt"
    model = YOLO(model_weight, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    # Inspect flagship failure image
    inspect_geometric_properties(
        "data/processed/sod/val/images/000552.jpg",
        net,
        device,
        pixel_thresh_high=0.85,
        pixel_thresh_low=0.40,
    )

    # Inspect false positive tiles
    inspect_geometric_properties(
        "data/processed/sod_tiled/images/val/000707_t2.png",
        net,
        device,
        pixel_thresh_high=0.85,
        pixel_thresh_low=0.40,
    )
    inspect_geometric_properties(
        "data/processed/sod_tiled/images/val/000784_t2.png",
        net,
        device,
        pixel_thresh_high=0.85,
        pixel_thresh_low=0.40,
    )


if __name__ == "__main__":
    run_inspection()
