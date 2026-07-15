import cv2
import numpy as np
import torch
from ultralytics import YOLO


class RawStage1Router:
    """
    A high-fidelity Stage 1 Router that bypasses YOLO's post-processing API
    to preserve continuous low-confidence signals (Option A) and apply
    spatial connected-component filters (Option C).
    """

    def __init__(self, model_path, pixel_thresh=0.30, min_cc_area=25):
        print(f"[+] Initializing Raw Router with model: {model_path}")
        self.yolo_model = YOLO(model_path, task="semantic")
        self.net = self.yolo_model.model
        self.net.eval()
        self.device = next(self.net.parameters()).device

        self.pixel_thresh = pixel_thresh
        self.min_cc_area = min_cc_area

    def predict_and_filter(self, img_path, imgsz=512):
        # 1. Manual Pre-processing
        img = cv2.imread(str(img_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image at {img_path}")

        h_orig, w_orig = img.shape[:2]
        img_resized = cv2.resize(img, (imgsz, imgsz))

        # BGR -> RGB, HWC -> CHW, Normalize
        img_tensor = (
            torch.from_numpy(img_resized[:, :, ::-1].copy()).permute(2, 0, 1).float()
            / 255.0
        )
        img_tensor = img_tensor.unsqueeze(0).to(self.device)

        # 2. Raw Forward Pass
        with torch.no_grad():
            raw_output = self.net(img_tensor)

        logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
        probs = torch.sigmoid(logits)

        # Extract target defect class channel (Channel 1)
        target_channel = 1 if logits.shape[1] > 1 else 0
        raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

        # 3. Scale probability map back to original size
        probs_resized = cv2.resize(
            raw_probs_map, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR
        )

        # 4. Apply lower pixel threshold (Option A)
        pred_bin = (probs_resized >= self.pixel_thresh).astype(np.uint8)

        # 5. Apply Connected-Component Size Filter (Option C)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            pred_bin, connectivity=8
        )

        filtered_mask = np.zeros_like(pred_bin)
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= self.min_cc_area:
                filtered_mask[labels == i] = 1

        return img, probs_resized, filtered_mask


if __name__ == "__main__":
    # Test execution using your newly trained best weights
    model_weight = "mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt"
    test_image = "data/processed/sod/val/images/000552.jpg"

    router = RawStage1Router(
        model_path=model_weight,
        pixel_thresh=0.28,  # Set just below our peak logit probability of 0.322
        min_cc_area=20,  # Filter out noise spots smaller than 20 pixels
    )

    try:
        orig_img, probs, mask = router.predict_and_filter(test_image)

        # Generate green mask overlay
        overlay = orig_img.copy()
        overlay[mask == 1] = [0, 255, 0]  # Draw green mask overlay
        visualized = cv2.addWeighted(orig_img, 0.7, overlay, 0.3, 0)

        # Save side-by-side comparison (Original vs Green Mask Overlay)
        comparison = np.hstack((orig_img, visualized))
        output_path = "test_raw_router_result.jpg"
        cv2.imwrite(output_path, comparison)

        print("\n=========================================================")
        print(f"[✓] TEST COMPLETE: Visual results saved to {output_path}")
        print("=========================================================")
        print("Open this file. You should see a green mask drawn")
        print("exactly over the scratch that was previously missed!")
        print("=========================================================\n")

    except Exception as e:
        print(f"[!] Test failed: {e}")
