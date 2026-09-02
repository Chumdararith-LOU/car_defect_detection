"""Real-time Stage 2 (defect classes) inference on a video file.

Display-only: draws instance masks + labels on each frame in a window.
Nothing is written to disk.

Usage:
    python tools/video_stage2_live.py --video path/to/video.mp4
    python tools/video_stage2_live.py --video v.mp4 --conf 0.2 --imgsz 640 --skip 2

Controls: q / ESC = quit
"""

import argparse
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_CANDIDATES = [
    REPO_ROOT / "backend" / "models" / "stage2" / "deployed.pt",
    REPO_ROOT / "backend" / "models" / "stage2" / "best.pt",
]


def resolve_model_path(explicit):
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(f"Model not found: {p}")
        return p
    for cand in DEFAULT_MODEL_CANDIDATES:
        if cand.exists():
            return cand
    stage2_dir = REPO_ROOT / "backend" / "models" / "stage2"
    pts = sorted(stage2_dir.glob("*.pt")) if stage2_dir.exists() else []
    if not pts:
        raise FileNotFoundError("No Stage 2 weights found under backend/models/stage2/")
    return pts[0]


def main():
    ap = argparse.ArgumentParser(
        description="Live Stage 2 defect inference on video (no saving)."
    )
    ap.add_argument("--video", required=True, help="Path to the .mp4 file")
    ap.add_argument(
        "--model", default=None, help="Stage 2 .pt path (default: auto-detect)"
    )
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, default=1024, help="1024=accuracy, 640=faster")
    ap.add_argument("--device", default="", help="mps / cuda / cpu (default: auto)")
    ap.add_argument(
        "--skip", type=int, default=1, help="Process every Nth frame (speed)"
    )
    args = ap.parse_args()

    model_path = resolve_model_path(args.model)
    print(f"[video_live] model: {model_path}")
    print(f"[video_live] video: {args.video}")

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {args.video}")

    model = YOLO(str(model_path))

    last_annotated = None
    ema_ms = None
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % args.skip == 0:
            t0 = time.time()
            results = model(
                frame,
                imgsz=args.imgsz,
                conf=args.conf,
                device=args.device or None,
                verbose=False,
            )
            ms = (time.time() - t0) * 1000
            ema_ms = ms if ema_ms is None else 0.8 * ema_ms + 0.2 * ms
            last_annotated = results[0].plot()  # masks + boxes + labels

        show = last_annotated if last_annotated is not None else frame
        if ema_ms is not None:
            txt = f"Stage2 {1000.0 / ema_ms:.1f} FPS (infer {ema_ms:.0f} ms)"
            cv2.putText(
                show, txt, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )

        cv2.imshow("Stage 2 Live Inference", show)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()
    print("[video_live] done.")


if __name__ == "__main__":
    main()
