"""Fetch and verify production model weights.

Primary path: resolve Git LFS pointer files via ``git lfs pull`` (the weights
are stored in this repo with Git LFS). Fallback path: if a ``--source-url``
base is provided, download each weight over HTTP from
``{source_url}/{stage}/{filename}`` (for GitHub Releases / Hugging Face Hub
mirrors). After fetching, every weight is SHA-256-verified against
``models/manifest.json``.

Usage:
    python scripts/download_models.py                      # use git lfs pull
    python scripts/download_models.py --source-url https://example.com/weights
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "models" / "manifest.json"

# Files smaller than this (and LFS pointer files) are considered "not fetched".
_MIN_REAL_SIZE = 1024 * 1024  # 1 MB


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    """Return True if the file is a Git LFS pointer (not the real weight)."""
    try:
        with open(path, "rb") as f:
            head = f.read(64)
        return head.startswith(b"version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


def needs_fetch(path: Path) -> bool:
    return (
        not path.exists()
        or is_lfs_pointer(path)
        or path.stat().st_size < _MIN_REAL_SIZE
    )


def git_lfs_available() -> bool:
    return shutil.which("git-lfs") is not None


def git_lfs_pull(rel_path: str) -> bool:
    """Resolve a single LFS pointer file. Returns True on success."""
    try:
        subprocess.run(
            ["git", "lfs", "pull", "--include", rel_path],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"    git lfs pull failed: {e.stderr.decode().strip()}")
        return False


def download_http(url: str, dest: Path) -> bool:
    try:
        print(f"    downloading {url}")
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"    download failed: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-url",
        default=None,
        help="Optional HTTP base URL mirror for weights "
        "(e.g. a GitHub Releases asset base or HF Hub URL).",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text())
    have_lfs = git_lfs_available()
    if not have_lfs:
        print("WARNING: git-lfs not found on PATH. Install with `brew install git-lfs`.")
        if not args.source_url:
            print("Without git-lfs or --source-url, weights cannot be fetched.")

    ok, failed = 0, 0
    for m in manifest["models"]:
        rel = f"models/{m['stage']}/{m['filename']}"
        dest = ROOT / rel
        name = m["name"]

        if not needs_fetch(dest):
            print(f"[OK]   {name} already present")
        else:
            print(f"[FETCH] {name} -> {rel}")
            fetched = False
            if have_lfs:
                fetched = git_lfs_pull(rel)
            if not fetched and args.source_url:
                url = f"{args.source_url.rstrip('/')}/{m['stage']}/{m['filename']}"
                fetched = download_http(url, dest)
            if not fetched:
                print(f"    could not fetch {name}")
                failed += 1
                continue

        # Verify checksum.
        expected = m.get("sha256")
        if expected:
            actual = sha256_of(dest)
            if actual == expected:
                print(f"    sha256 verified ({actual[:12]}...)")
                ok += 1
            else:
                print(f"    SHA256 MISMATCH: expected {expected[:12]}... got {actual[:12]}...")
                failed += 1
        else:
            ok += 1

    print("\n==== SUMMARY ====")
    print(f"Verified: {ok}   Failed: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
