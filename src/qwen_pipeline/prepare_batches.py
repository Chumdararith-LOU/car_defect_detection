import json
import shutil
from pathlib import Path

SOURCE_IMG_DIR = Path("data/raw_images_to_process")
OUTPUT_BASE_DIR = Path("../../data/qwen_staging")
CHUNK_SIZE = 100

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def chunk_list(data, size):
    """Yield successive chunks of a specific size from a list."""
    for i in range(0, len(data), size):
        yield data[i : i + size]


def main():
    if not SOURCE_IMG_DIR.exists():
        print(f"[!] Source directory '{SOURCE_IMG_DIR}' does not exist.")
        return

    # 1. Gather all valid images
    print(f"[*] Scanning '{SOURCE_IMG_DIR}' for images...")
    all_images = []
    for ext in VALID_EXTENSIONS:
        all_images.extend(list(SOURCE_IMG_DIR.rglob(f"*{ext}")))
        all_images.extend(list(SOURCE_IMG_DIR.rglob(f"*{ext.upper()}")))

    # Deduplicate in case of upper/lower case extension overlap
    all_images = list(set(all_images))
    all_images.sort()  # Ensure deterministic batching

    total_images = len(all_images)
    if total_images == 0:
        print("[!] No images found.")
        return

    print(f"[*] Found {total_images} images. Splitting into chunks of {CHUNK_SIZE}...")

    OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Process in chunks
    batches = list(chunk_list(all_images, CHUNK_SIZE))

    for batch_idx, image_paths in enumerate(batches, start=1):
        batch_name = f"batch_{batch_idx:03d}"
        batch_dir = OUTPUT_BASE_DIR / batch_name
        batch_dir.mkdir(parents=True, exist_ok=True)

        manifest_data = {
            "batch_id": batch_name,
            "total_images": len(image_paths),
            "images": [],
        }

        print(f"  -> Building {batch_name} ({len(image_paths)} images)...")

        for img_idx, src_path in enumerate(image_paths, start=1):
            unique_img_id = f"{batch_name}_img_{img_idx:04d}"
            dest_filename = src_path.name
            dest_path = batch_dir / dest_filename

            # Copy image to flatten the structure for the server
            shutil.copy2(src_path, dest_path)

            manifest_data["images"].append(
                {"id": unique_img_id, "filename": dest_filename}
            )

        # 3. Write manifest.json
        manifest_path = batch_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=4)

    print("-" * 50)
    print(f"[✓] Successfully generated {len(batches)} batches in '{OUTPUT_BASE_DIR}'")
    print("[*] Next step: Transfer the first batch to your RTX 3090 server.")
    print(
        "    Example: rsync -avP {OUTPUT_BASE_DIR}/batch_001 user@server_ip:/path/to/project/qwen_prelabels/"
    )


if __name__ == "__main__":
    main()
