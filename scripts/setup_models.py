#!/usr/bin/env python3
"""
Download and verify champion models for a fresh clone.
Usage: python scripts/setup_models.py
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "configs" / "models" / "champion_models.json"
MODELS_DIR = REPO_ROOT / "backend" / "models"


def get_release_url(tag: str, filename: str) -> str:
    return f"https://github.com/Chumdararith-LOU/car_defect_detection/releases/download/{tag}/{filename}"


def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash


def main():
    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    release_tag = manifest.get("release_tag", "v1.0.0-models")
    print(f"🚀 Setting up champion models (Release: {release_tag})...")
    all_good = True

    for model in manifest["models"]:
        stage = model["stage"]
        filename = model["filename"]
        expected_hash = model["sha256"]

        target_dir = MODELS_DIR / stage
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        # Check if already exists and valid
        if target_path.exists() and verify_sha256(target_path, expected_hash):
            print(f"✅ {stage}/{filename} (verified)")
            continue

        # Download
        url = get_release_url(release_tag, filename)
        print(f"⬇️  Downloading {stage}/{filename}...")
        try:
            urllib.request.urlretrieve(url, target_path)
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            all_good = False
            continue

        # Verify
        if verify_sha256(target_path, expected_hash):
            print(f"✅ {stage}/{filename} (downloaded & verified)")
        else:
            print(f"❌ SHA-256 mismatch for {filename}!")
            target_path.unlink(missing_ok=True)
            all_good = False

    # Create deployed.pt relative symlinks
    print("\n🔗 Setting up deployment symlinks...")
    for stage_dir in MODELS_DIR.iterdir():
        if stage_dir.is_dir() and stage_dir.name.startswith("stage"):
            champions = list(stage_dir.glob("*_champion.pt"))
            if champions:
                champ_name = champions[0].name
                deployed_link = stage_dir / "deployed.pt"
                if deployed_link.exists() or deployed_link.is_symlink():
                    deployed_link.unlink()
                deployed_link.symlink_to(champ_name)
                print(f"✅ {stage_dir.name}/deployed.pt -> {champ_name}")

    if all_good:
        print("\n🎉 All models ready! You can now start the backend.")
    else:
        print("\n⚠️  Some models failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
