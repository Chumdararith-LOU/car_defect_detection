import cv2
import numpy as np
from ultralytics import YOLO
from stage1.utils.config_helpers import load_pipeline_config, resolve_device


def get_stitched_probability_map(img, yolo_model, device, overlap_frac=0.15, imgsz=640):
    """
    Slices input image into 4 overlapping quadrants, runs model inference,
    and stitches continuous probability maps to prevent receptive field dilution.
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

        results = yolo_model(tile_crop, device=device, verbose=False, imgsz=imgsz)
        res = results[0]

        if hasattr(res, "semantic_mask") and res.semantic_mask is not None:
            tile_prob = res.semantic_mask.data.cpu().numpy().squeeze()
        elif hasattr(res, "masks") and res.masks is not None:
            tile_prob = res.masks.data[0].cpu().numpy().squeeze()
        else:
            tile_prob = np.zeros((imgsz, imgsz), dtype=np.float32)

        if tile_prob.shape[:2] != (t_h, t_w):
            tile_prob = cv2.resize(
                tile_prob, (t_w, t_h), interpolation=cv2.INTER_LINEAR
            )

        global_probs[y0:y1, x0:x1] = np.maximum(global_probs[y0:y1, x0:x1], tile_prob)

    return global_probs


class RawStage1Router:
    """
    A high-fidelity Stage 1 Router that uses relative argmax channel selection
    to natively extract micro-defects and large structural anomalies.
    """

    def __init__(self, model_path, overlap_frac=0.15, device=None):
        print(f"[+] Initializing Raw Stage 1 Router with model: {model_path}")
        self.yolo_model = YOLO(model_path, task="semantic")
        self.net = self.yolo_model.model
        self.net.eval()

        self.device = (
            device if device is not None else next(self.net.parameters()).device
        )

        self.net.to(self.device)
        print(f"[*] Stage 1 Router successfully bound to device: {self.device}")
        self.overlap_frac = overlap_frac

    @classmethod
    def from_config(
        cls, config_path="configs/pipeline_config.yaml", model_path_override=None
    ):
        """Creates a router instance directly using parameters defined in configs/pipeline_config.yaml."""
        cfg = load_pipeline_config(config_path)
        dataset = cfg.get("dataset", {})
        model_cfg = cfg.get("model", {})

        model_path = model_path_override or model_cfg.get("preset", "yolo26n-sem.pt")
        overlap_val = dataset.get("overlap_percent", 0.15)
        device = resolve_device(cfg)

        return cls(
            model_path=model_path,
            overlap_frac=overlap_val,
            device=device,
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
        """Slices, runs inference, and stitches probabilities back to full resolution."""
        return get_stitched_probability_map(
            img, self.yolo_model, self.device, self.overlap_frac, imgsz
        )

    def run_hysteresis_gate(self, global_probs, tau_high=0.35, tau_low=0.15):
        """
        True double-threshold Hysteresis Gating.
        Seeds are anchored at >= tau_high and expanded along paths >= tau_low.
        """
        high_seeds = (global_probs >= tau_high).astype(np.uint8)
        low_pathways = (global_probs >= tau_low).astype(np.uint8)

        if not np.any(high_seeds):
            return np.zeros_like(global_probs, dtype=np.uint8)

        num_labels, labels, _, _ = cv2.connectedComponentsWithStats(low_pathways)
        final_mask = np.zeros_like(global_probs, dtype=np.uint8)

        for label_idx in range(1, num_labels):
            component_mask = labels == label_idx
            if np.any(high_seeds[component_mask]):
                final_mask[component_mask] = 1

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
        output_path = "test_argmax_router_result.jpg"
        cv2.imwrite(output_path, comparison)

        print("\n" + "=" * 70)
        print(" 🎯 RELATIVE ARGMAX ROUTER EVALUATION COMPLETE")
        print("=" * 70)
        print(f"Defect Detected / Stage 2 Triggered: {triggered}")
        print(f"Visualized side-by-side results saved to: {output_path}")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"[!] Evaluation failed: {e}")
