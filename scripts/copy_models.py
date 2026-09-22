"""Copy production model weights from the source R&D repo into models/.

Reads models/manifest.json, copies each model checkpoint from its source
location, computes a SHA-256 checksum, and writes the checksum back into the
manifest for later integrity verification.

Usage:
    python scripts/copy_models.py [--source-root /path/to/car_defect_detection]
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "models" / "manifest.json"

DEFAULT_SOURCE_ROOT = (
    "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection"
)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=DEFAULT_SOURCE_ROOT)
    args = parser.parse_args()
    source_root = Path(args.source_root)

    if not source_root.exists():
        print(f"ERROR: source root not found: {source_root}")
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text())
    copied, missing = [], []

    for model in manifest["models"]:
        src = source_root / model["source"]
        dest_dir = ROOT / "models" / model["stage"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / model["filename"]

        if not src.exists():
            missing.append((model["name"], str(src)))
            print(f"[MISSING] {model['name']}: {src}")
            continue

        print(f"[COPY] {model['name']}: {src.name} -> {dest}")
        shutil.copy2(src, dest)
        checksum = sha256_of(dest)
        model["sha256"] = checksum
        size_mb = dest.stat().st_size / (1024 * 1024)
        copied.append((model["name"], f"{size_mb:.1f} MB", checksum[:12]))
        print(f"         {size_mb:.1f} MB  sha256={checksum[:12]}...")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print("\n==== SUMMARY ====")
    print(f"Copied: {len(copied)}")
    for name, size, cs in copied:
        print(f"  {name}: {size} (sha256 {cs}...)")
    if missing:
        print(f"Missing: {len(missing)}")
        for name, path in missing:
            print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
