import cv2
import numpy as np
import argparse
from pathlib import Path
from src.inference.router import RawStage1Router

# =====================================================================
# MODULAR MODEL CONFIGURATION
# Add or remove models here to dynamically alter the side-by-side output
# =====================================================================
MODELS_TO_COMPARE = [
    {
        "id": "Model 1: yolo26n 1024 (Focal)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/122e3f76a2ee4d6abbcc94698b217266/artifacts/weights/best.pt",
        "imgsz": 1024,
        "high": 0.47,
        "low": 0.35,
    },
    {
        "id": "Model 3: yolo26m 640 (Focal)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt",
        "imgsz": 640,
        "high": 0.28,
        "low": 0.18,
    },
    {
        "id": "Model 6: yolo26n 640 (CE)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/0b8ace4baec142448ce7e06434938ac2/artifacts/weights/best.pt",
        "imgsz": 640,
        "high": 0.70,
        "low": 0.70,
    },
]


def add_header(image, title, status_text, is_detected):
    """Adds a dark header bar with the model name and detection status."""
    h, w = image.shape[:2]
    header_height = 80
    header = np.zeros((header_height, w, 3), dtype=np.uint8)

    # Background colors: Dark Gray default, Dark Red if defect detected
    bg_color = (0, 0, 100) if is_detected else (40, 40, 40)
    header[:] = bg_color

    # Write Model Title
    cv2.putText(
        header, title, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
    )

    # Write Detection Status
    status_color = (0, 255, 0) if is_detected else (200, 200, 200)
    cv2.putText(
        header, status_text, (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2
    )

    return np.vstack((header, image))


def generate_comparison(img_path, output_filename, device="cuda:0"):
    img_path = Path(img_path)
    if not img_path.exists():
        print(f"[!] Image not found: {img_path}")
        return

    print(f"[*] Processing visual comparison for: {img_path.name}")
    orig_img = cv2.imread(str(img_path))

    # Base layout starts with the original untouched image
    panels = [
        add_header(orig_img.copy(), "Original Image", "Ground Truth / Input", False)
    ]

    for cfg in MODELS_TO_COMPARE:
        print(f"    -> Running {cfg['id']}...")

        # Initialize the router dynamically for this specific model's thresholds
        router = RawStage1Router(
            model_path=cfg["path"],
            pixel_thresh_high=cfg["high"],
            pixel_thresh_low=cfg["low"],
            min_cc_area=20,  # Morphological noise rejection limit
            max_cc_area_reject=5000,
            device=device,
        )

        # Extract the final masked prediction
        _, _, final_mask, has_defect = router.route_image(img_path, imgsz=cfg["imgsz"])

        # Paint the overlay neon green
        overlay = orig_img.copy()
        overlay[final_mask == 1] = [0, 255, 0]  # BGR format
        visualized = cv2.addWeighted(orig_img, 0.6, overlay, 0.4, 0)

        status_msg = "TRIGGERED (Defect Found)" if has_defect else "CLEAN (Passed Gate)"

        # Attach header and append to horizontal layout
        panel = add_header(visualized, cfg["id"], status_msg, has_defect)
        panels.append(panel)

    # Stitch all images side-by-side
    final_stitched_image = np.hstack(panels)

    cv2.imwrite(output_filename, final_stitched_image)
    print(f"[+] Successfully saved comparison graphic to: {output_filename}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Side-by-Side Model Tradeoff Visuals"
    )
    parser.add_argument(
        "--image", type=str, required=True, help="Path to the target test image"
    )
    parser.add_argument(
        "--output", type=str, default="tradeoff_comparison.jpg", help="Output filename"
    )
    parser.add_argument(
        "--device", type=str, default="cuda:0", help="Hardware execution target"
    )
    args = parser.parse_args()

    generate_comparison(args.image, args.output, args.device)
