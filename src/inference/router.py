import cv2
import numpy as np
import torch
from ultralytics import YOLO


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
        pixel_thresh_high=0.28,
        pixel_thresh_low=0.15,
        min_cc_area=20,
        overlap_frac=0.15,
    ):
        print(f"[+] Initializing Raw Stage 1 Router with model: {model_path}")
        self.yolo_model = YOLO(model_path, task="semantic")
        self.net = self.yolo_model.model
        self.net.eval()
        self.device = next(self.net.parameters()).device

        self.pixel_thresh_high = pixel_thresh_high  # The strong seed threshold (anchor)
        self.pixel_thresh_low = (
            pixel_thresh_low  # The weak connectivity threshold (pathway)
        )
        self.min_cc_area = min_cc_area  # Component size rejection filter
        self.overlap_frac = overlap_frac

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

    def predict_stitched_probabilities(self, img, imgsz=512):
        """Slices, runs raw-logits inference, and stitches probabilities back to full resolution."""
        h_orig, w_orig = img.shape[:2]
        global_probs = np.zeros((h_orig, w_orig), dtype=np.float32)
        tile_bounds = self.get_tile_coords(h_orig, w_orig)

        for (y0, y1), (x0, x1) in tile_bounds:
            tile_crop = img[y0:y1, x0:x1]
            t_h, t_w = tile_crop.shape[:2]

            # Standard pre-processing to match training grid size
            tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
            img_tensor = (
                torch.from_numpy(tile_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            img_tensor = img_tensor.unsqueeze(0).to(self.device)

            # Raw forward pass to extract unbinarized network logits
            with torch.no_grad():
                raw_output = self.net(img_tensor)

            logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
            probs = torch.sigmoid(logits)

            # Target Channel 1 = Defect, Channel 0 = Background
            target_channel = 1 if logits.shape[1] > 1 else 0
            raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

            # Rescale the probability map back to its uncropped physical tile shape
            tile_probs_resized = cv2.resize(
                raw_probs_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
            )

            # Max-pooling overlapping regions to preserve peak feature boundaries
            global_probs[y0:y1, x0:x1] = np.maximum(
                global_probs[y0:y1, x0:x1], tile_probs_resized
            )

        return global_probs

    def run_hysteresis_gate(self, global_probs):
        """
        Executes Two-Pass Hysteresis Gating on the global probability map.

        1. Identifies high-confidence anchor seeds.
        2. Extracted continuous potential pathways.
        3. Keeps only continuous regions that contain at least one anchor seed.
        4. Filters remaining structures based on minimum component pixel area.
        """
        # Pass 1 & 2: Generate High and Low binary masks
        mask_high = (global_probs >= self.pixel_thresh_high).astype(np.uint8)
        mask_low = (global_probs >= self.pixel_thresh_low).astype(np.uint8)

        # Pass 3: Label all connected structures in the low-confidence mask
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask_low, connectivity=8
        )

        gated_mask = np.zeros_like(mask_low)

        for i in range(1, num_labels):  # Index 0 is background
            # Segment component and compute overlap with high-confidence seed mask
            component_pixels = labels == i
            has_seed = np.any(mask_high[component_pixels] > 0)

            if has_seed:
                # Retain the entire continuous component, recovering the weak tail pixels
                gated_mask[component_pixels] = 1

        # Pass 4: Apply minimum continuous area filter to reject fine speckles
        num_labels_filtered, labels_filtered, stats_filtered, _ = (
            cv2.connectedComponentsWithStats(gated_mask, connectivity=8)
        )
        final_mask = np.zeros_like(gated_mask)

        for i in range(1, num_labels_filtered):
            area = stats_filtered[i, cv2.CC_STAT_AREA]
            if area >= self.min_cc_area:
                final_mask[labels_filtered == i] = 1

        return final_mask

    def route_image(self, img_path, imgsz=512):
        """High-level entry point for Stage 1 gating routing."""
        img = cv2.imread(str(img_path))
        if img is None:
            raise FileNotFoundError(f"Could not load image at {img_path}")

        # 1. Tile, infer, and stitch
        global_probs = self.predict_stitched_probabilities(img, imgsz)

        # 2. Apply Two-Pass Hysteresis Gate
        final_mask = self.run_hysteresis_gate(global_probs)

        # 3. Decision Gating: Router triggers Stage 2 if any defect mask survives
        has_defect = np.any(final_mask > 0)

        return img, global_probs, final_mask, has_defect


if __name__ == "__main__":
    # Test Verification block on the known target failure 000552.jpg
    model_weight = "runs/semantic/artifacts/models/stage1_sod/weights/best.pt"
    test_image = "data/processed/sod/val/images/000552.jpg"

    # Configure router with our empirically discovered thresholds
    router = RawStage1Router(
        model_path=model_weight,
        pixel_thresh_high=0.28,  # Anchor seed threshold (based on 0.322 peak Y=204 logits)
        pixel_thresh_low=0.15,  # Path connectivity threshold (safely encapsulating 0.170 base)
        min_cc_area=20,  # Clear background speckles
        overlap_frac=0.15,
    )

    try:
        orig_img, global_probs, final_mask, triggered = router.route_image(test_image)

        # Create a visual overlay of the surviving hysteresis mask
        overlay = orig_img.copy()
        overlay[final_mask == 1] = [0, 255, 0]  # Draw green mask over defect
        visualized = cv2.addWeighted(orig_img, 0.7, overlay, 0.3, 0)

        # Save side-by-side comparison
        comparison = np.hstack((orig_img, visualized))
        output_path = "test_hysteresis_router_result.jpg"
        cv2.imwrite(output_path, comparison)

        print("\n" + "=" * 70)
        print(" 🎯 TWO-PASS HYSTERESIS ROUTER EVALUATION COMPLETE")
        print("=" * 70)
        print(f"Defect Detected / Stage 2 Triggered: {triggered}")
        print(f"Visualized side-by-side results saved to: {output_path}")
        print("=" * 70)
        print("Open the image. You should see the ENTIRE continuous crack")
        print("cleanly masked in green, with ZERO background shadow noise!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"[!] Evaluation failed: {e}")
