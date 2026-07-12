import cv2
import numpy as np
from pathlib import Path


class Stage1GatingRouter:
    """
    The decision gating routing engine running downstream inference gates.
    Now equipped with Near-Miss logging to catch threshold miscalibrations.
    """

    def __init__(
        self,
        pixel_thresh=0.70,
        anomaly_thresh=0.0005,
        near_miss_margin=0.20,
        log_dir="artifacts/near_misses",
    ):
        self.pixel_thresh = pixel_thresh
        self.anomaly_thresh = anomaly_thresh
        self.near_miss_margin = near_miss_margin

        # Setup logging directory for borderline cases
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def route_frame(self, frame_id, original_image, predicted_saliency_map):
        """
        Determines if the frame requires Stage 2 processing and logs borderline cases.

        Args:
            frame_id (str): Unique identifier for the image (e.g., "004000").
            original_image (np.ndarray): The raw BGR image for saving if flagged.
            predicted_saliency_map (np.ndarray): 2D array [H, W] of float predictions in [0, 1].
        """
        h, w = predicted_saliency_map.shape
        total_pixels = h * w

        # Threshold pixel activations
        active_pixels = np.sum(predicted_saliency_map >= self.pixel_thresh)

        # Calculate global saliency score
        saliency_score = active_pixels / total_pixels

        # 1. Active Route Decision
        trigger_stage2 = saliency_score >= self.anomaly_thresh
        routing_state = "ACTIVE_ROUTE" if trigger_stage2 else "PASS_ROUTE"

        # 2. Near-Miss Logging Logic
        near_miss = False
        if not trigger_stage2:
            lower_bound = self.anomaly_thresh * (1.0 - self.near_miss_margin)
            if lower_bound <= saliency_score < self.anomaly_thresh:
                near_miss = True
                # Log the pristine-but-suspicious image for manual human review
                save_path = (
                    self.log_dir / f"near_miss_{saliency_score:.6f}_{frame_id}.jpg"
                )
                cv2.imwrite(str(save_path), original_image)
                print(f"[!] Near-Miss Logged: {frame_id} (Score: {saliency_score:.6f})")

        return {
            "saliency_score": float(saliency_score),
            "routing_state": routing_state,
            "trigger_stage2": bool(trigger_stage2),
            "is_near_miss": near_miss,
        }


# Execution test block
if __name__ == "__main__":
    # Simulate an image and a saliency map
    mock_image = np.zeros((1024, 1024, 3), dtype=np.uint8)
    mock_saliency = np.zeros((1024, 1024), dtype=np.float32)

    # Simulate a score of 0.00045 (which is 90% of the 0.00050 threshold)
    active_pixel_count = int(1024 * 1024 * 0.00045)
    mock_saliency.flat[:active_pixel_count] = 0.95

    router = Stage1GatingRouter(
        pixel_thresh=0.70, anomaly_thresh=0.0005, near_miss_margin=0.20
    )
    decision = router.route_frame("test_frame", mock_image, mock_saliency)

    print(f"Saliency Score: {decision['saliency_score']:.6f}")
    print(f"Routing Decision: {decision['routing_state']}")
    print(f"Was this a near-miss? {decision['is_near_miss']}")
    # Expected output: PASS_ROUTE (because 0.00045 < 0.00050), but is_near_miss = True
