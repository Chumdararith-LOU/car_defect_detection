"""Verify that the objectness-branch checkpoint unpickles with the custom head.

Usage:
    python scripts/verify_objectness_head.py /path/to/best.pt
"""
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `app.*` imports resolve.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.head_registry import register_custom_head  # noqa: E402

register_custom_head()

DEFAULT_CKPT = (
    "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/"
    "car_defect_detection/runs/segment/seesaw_surgical_objectness-26/weights/best.pt"
)


def main() -> None:
    ckpt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CKPT
    print(f"Loading checkpoint: {ckpt}")

    from ultralytics import YOLO

    model = YOLO(ckpt)

    # Find the head by locating the module that carries cv_obj (robust to layout).
    head = None
    for m in model.model.model:
        if hasattr(m, "cv_obj"):
            head = m
            break
    if head is None:
        head = model.model.model[-1]

    print(f"Head type: {type(head).__module__}.{type(head).__name__}")
    print(f"Has cv_obj: {hasattr(head, 'cv_obj')}")

    if hasattr(head, "cv_obj"):
        for i, conv in enumerate(head.cv_obj):
            b = conv.bias.detach().cpu().numpy()
            print(f"  cv_obj[{i}] bias = {b.item():.4f}")
        print("VERIFICATION PASSED")
    else:
        print("VERIFICATION FAILED: no cv_obj on head")


if __name__ == "__main__":
    main()
