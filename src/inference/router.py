import cv2
import numpy as np
import torch
from ultralytics import YOLO
from src.utils.config_helpers import load_pipeline_config


def get_stitched_probability_map(img, net, device, overlap_frac=0.15, imgsz=512):
    """
    Consolidated mathematical utility for slicing, raw inference,
    dynamic channel activation (Sigmoid/Softmax), and coordinate stitching.
    This guarantees identical probability space across training, profiling, and routing.
    """
    h_orig, w_orig = img.shape[:2]
    global_probs = np.zeros((h_orig, w_orig), dtype=np.float32)

    h_mid, w_mid = h_orig // 2, w_orig // 2
    oh, ow = int(h_orig * overlap_frac), int(w_orig * overlap_frac)
    tile_bounds = [
        ((0, min(h_orig, h_mid + oh)), (0, min(w_orig, w_mid + ow))),  # Top-Left
        ((0, min(h_orig, h_mid + oh)), (max(0, w_mid - ow), w_orig)),  # Top-Right
        ((max(0, h_mid - oh), h_orig), (0, min(w_orig, w_mid + ow))),  # Bottom-Left
        ((max(0, h_mid - oh), h_orig), (max(0, w_mid - ow), w_orig)),  # Bottom-Right
    ]

    for (y0, y1), (x0, x1) in tile_bounds:
        tile_crop = img[y0:y1, x0:x1]
        t_h, t_w = tile_crop.shape[:2]

        tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
        img_tensor = (
            (
                torch.from_numpy(tile_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            .unsqueeze(0)
            .to(device)
        )

        with torch.no_grad():
            raw_output = net(img_tensor)

        logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output

        if logits.shape[1] == 1:
            extended_logits = torch.cat([torch.zeros_like(logits), logits], dim=1)
            probs = torch.softmax(extended_logits, dim=1)
            raw_probs_map = probs[0, 1, :, :].cpu().numpy()
        else:
            probs = torch.softmax(logits, dim=1)
            raw_probs_map = probs[0, 1, :, :].cpu().numpy()

        tile_probs_resized = cv2.resize(
            raw_probs_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
        )

        global_probs[y0:y1, x0:x1] = np.maximum(
            global_probs[y0:y1, x0:x1], tile_probs_resized
        )

    return global_probs


class RawStage1Router:
    """
    A high-fidelity Stage 1 Router that bypasses YOLO's post-processing API.

    This router:
      1. Slices full-resolution images into overlapping quadrants.
      2. Runs raw-logits inference on each quadrant at training resolution (imgsz).
      3. Scales and coordinate-stitches tile probabilities into a global map.
      4. Applies a two-pass Hysteresis Thresholding Gate to recover low-confidence,
         continuous defect structures while rejecting unseeded background noise.
    """

    def __init__(
        self,
        model_path,
        pixel_thresh_high=0.47,
        pixel_thresh_low=0.35,
        min_cc_area=20,
        max_cc_area_reject=5000,
        overlap_frac=0.15,
    ):
        print(f"[+] Initializing Raw Stage 1 Router with model: {model_path}")
        self.yolo_model = YOLO(model_path, task="semantic")
        self.net = self.yolo_model.model
        self.net.eval()
        self.device = next(self.net.parameters()).device

        self.pixel_thresh_high = pixel_thresh_high
        self.pixel_thresh_low = pixel_thresh_low
        self.min_cc_area = min_cc_area
        self.max_cc_area_reject = max_cc_area_reject
        self.overlap_frac = overlap_frac

    @classmethod
    def from_config(
        cls, config_path="configs/pipeline_config.yaml", model_path_override=None
    ):
        """Creates a router instance directly using parameters defined in configs/pipeline_config.yaml."""
        cfg = load_pipeline_config(config_path)

        gating = cfg.get("gating_thresholds", {})
        dataset = cfg.get("dataset", {})
        model_cfg = cfg.get("model", {})

        model_path = model_path_override or model_cfg.get("preset", "yolo26n-sem.pt")
        overlap_val = dataset.get("overlap_percent", 0.15)

        return cls(
            model_path=model_path,
            pixel_thresh_high=gating.get("pixel_thresh_high", 0.47),
            pixel_thresh_low=gating.get("pixel_thresh_low", 0.35),
            min_cc_area=gating.get("min_cc_area", 20),
            max_cc_area_reject=gating.get("max_cc_area_reject", 5000),
            overlap_frac=overlap_val,
        )

    def get_tile_coords(self, h, w):
        """Returns coordinate bounds ((y0, y1), (x0, x1)) for 4 overlapping quadrants."""
        h_mid, w_mid = h // 2, w // 2
        oh, ow = int(h * self.overlap_frac), int(w * self.overlap_frac)

        return [
            ((0, min(h, h_mid + oh)), (0, min(w, w_mid + ow))),  # Top-Left
            ((0, min(h, h_mid + oh)), (max(0, w_mid - ow), w)),  # Top-Right
            ((max(0, h_mid - oh), h), (0, min(w, w_mid + ow))),  # Bottom-Left
            ((max(0, h_mid - oh), h), (max(0, w_mid - ow), w)),  # Bottom-Right
        ]

    def predict_stitched_probabilities(self, img, imgsz):
        """Slices, runs raw-logits inference, and stitches probabilities back to full resolution."""
        return get_stitched_probability_map(
            img, self.net, self.device, self.overlap_frac, imgsz
        )

    def run_hysteresis_gate(self, global_probs):
        """
        Executes Two-Pass Hysteresis Gating on the global probability map.

        1. Identifies high-confidence anchor seeds.
        2. Extracted continuous potential pathways.
        3. Keeps only continuous regions that contain at least one anchor seed.
        4. Filters remaining structures based on minimum component pixel area.
        """
        mask_high = (global_probs >= self.pixel_thresh_high).astype(np.uint8)
        mask_low = (global_probs >= self.pixel_thresh_low).astype(np.uint8)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask_low, connectivity=8
        )

        gated_mask = np.zeros_like(mask_low)

        for i in range(1, num_labels):
            component_pixels = labels == i
            has_seed = np.any(mask_high[component_pixels] > 0)

            if has_seed:
                gated_mask[component_pixels] = 1

        num_labels_filtered, labels_filtered, stats_filtered, _ = (
            cv2.connectedComponentsWithStats(gated_mask, connectivity=8)
        )
        final_mask = np.zeros_like(gated_mask)

        for i in range(1, num_labels_filtered):
            area = stats_filtered[i, cv2.CC_STAT_AREA]

            if area < self.min_cc_area:
                continue

            if area > self.max_cc_area_reject:
                continue

            x, y, w, h_box, _ = stats_filtered[i]

            if area <= 120:
                aspect_ratio = (
                    max(float(h_box) / w, float(w) / h_box)
                    if (w > 0 and h_box > 0)
                    else 0
                )
                if aspect_ratio < 2.0:
                    continue

            final_mask[labels_filtered == i] = 1

        return final_mask

    def route_image(self, img_path, imgsz):
        """High-level entry point for Stage 1 gating routing."""
        img = cv2.imread(str(img_path))
        if img is None:
            raise FileNotFoundError(f"Could not load image at {img_path}")

        global_probs = self.predict_stitched_probabilities(img, imgsz)

        final_mask = self.run_hysteresis_gate(global_probs)

        has_defect = np.any(final_mask > 0)

        return img, global_probs, final_mask, has_defect


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Stage 1 Router Verification Utility")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/pipeline_config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--image",
        type=str,
        default="data/processed/sod/val/images/000552.jpg",
        help="Path to test image",
    )
    parser.add_argument(
        "--weights", type=str, default="yolo26n-sem.pt", help="Override weights path"
    )
    args = parser.parse_args()

    print(f"[*] Instantiating router from config: {args.config}")

    weights_path = args.weights
    if not os.path.exists(weights_path):
        print(
            f"[!] Target weights not found at: {weights_path}. Defaulting to configuration defaults."
        )
        weights_path = None

    try:
        router = RawStage1Router.from_config(
            config_path=args.config, model_path_override=weights_path
        )

        cfg = load_pipeline_config(args.config)
        imgsz = cfg.get("dataset", {}).get("imgsz", 640)

        print(f"[*] Running router routing on image: {args.image}")
        orig_img, global_probs, final_mask, triggered = router.route_image(
            args.image, imgsz=imgsz
        )

        overlay = orig_img.copy()
        overlay[final_mask == 1] = [0, 255, 0]
        visualized = cv2.addWeighted(orig_img, 0.7, overlay, 0.3, 0)

        comparison = np.hstack((orig_img, visualized))
        output_path = "test_hysteresis_router_result.jpg"
        cv2.imwrite(output_path, comparison)

        print("\n" + "=" * 70)
        print(" 🎯 TWO-PASS HYSTERESIS ROUTER EVALUATION COMPLETE")
        print("=" * 70)
        print(
            f"Active Gating: High={router.pixel_thresh_high} | Low={router.pixel_thresh_low} | Min Area={router.min_cc_area}"
        )
        print(f"Defect Detected / Stage 2 Triggered: {triggered}")
        print(f"Visualized side-by-side results saved to: {output_path}")
        print("=" * 70)
        print("Open the image to inspect the continuous crack geometry!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"[!] Evaluation failed: {e}")
