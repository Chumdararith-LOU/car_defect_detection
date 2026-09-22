"""Verify every model in the manifest is on disk, matches its checksum, and loads.

Usage:
    python scripts/verify_all_models.py [--device auto|cuda|mps|cpu]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.device import resolve_device  # noqa: E402
from app.core.model_registry import model_registry  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    device = resolve_device(args.device)
    print(f"Verifying models on device: {device}\n")

    passed, failed = 0, 0
    for info in model_registry.list_models():
        name = info["name"]
        stage = info["stage"]
        try:
            if not info["on_disk"]:
                raise FileNotFoundError("weights not on disk")
            if not model_registry.verify_checksum(name):
                raise ValueError("sha256 mismatch vs manifest")
            model = model_registry.get_model(name, device=device)
            print(f"[PASS] {name:<24} stage={stage:<7} type={type(model).__name__}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {name:<24} stage={stage:<7} error={e}")
            failed += 1

    print("\n==== SUMMARY ====")
    print(f"Passed: {passed}   Failed: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
