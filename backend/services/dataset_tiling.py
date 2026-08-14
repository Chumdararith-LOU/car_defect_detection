import logging
from pathlib import Path

import cv2
import yaml
from shapely.geometry import Polygon, box, MultiPolygon

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def _generate_tile_boxes(
    W: int, H: int, tile_size: int, overlap: float
) -> list[tuple[int, int, int, int]]:
    """Generate bounding boxes for tiles.
    If tile_size=0, uses legacy 2x2 adaptive halving from create_tiles.py."""
    boxes = []
    if tile_size > 0:
        stride = int(tile_size * (1 - overlap))
        for y in range(0, H, stride):
            for x in range(0, W, stride):
                x2 = min(x + tile_size, W)
                y2 = min(y + tile_size, H)
                x1 = max(0, x2 - tile_size)
                y1 = max(0, y2 - tile_size)
                boxes.append((x1, y1, x2, y2))
                if x2 == W:
                    break
            if y2 == H:
                break
    else:
        # Legacy 2x2 adaptive halving (preserves create_tiles.py edge case)
        h_mid, w_mid = H // 2, W // 2
        oh, ow = int(H * overlap), int(W * overlap)
        boxes = [
            (0, 0, min(W, w_mid + ow), min(H, h_mid + oh)),
            (max(0, w_mid - ow), 0, W, min(H, h_mid + oh)),
            (0, max(0, h_mid - oh), min(W, w_mid + ow), H),
            (max(0, w_mid - ow), max(0, h_mid - oh), W, H),
        ]
    return boxes


def _process_yolo_labels(lbl_path: Path, W: int, H: int) -> list[tuple[int, Polygon]]:
    """Parse YOLO .txt file into Shapely Polygons in pixel coordinates."""
    polygons = []
    if not lbl_path.exists():
        return polygons
    with open(lbl_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 7:  # class_id + at least 3 points (6 coords)
                continue
            cls_id = int(parts[0])
            coords = list(map(float, parts[1:]))
            pts = [(coords[i] * W, coords[i + 1] * H) for i in range(0, len(coords), 2)]
            poly = Polygon(pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if not poly.is_empty:
                polygons.append((cls_id, poly))
    return polygons


def _tile_single_image(
    img_path: Path,
    lbl_path: Path,
    mask_path: Path,
    out_img_dir: Path,
    out_lbl_dir: Path,
    out_mask_dir: Path,
    tile_size: int,
    overlap: float,
    min_area_ratio: float,
) -> int:
    """Slice one image and its corresponding labels/masks. Returns number of tiles saved."""
    img = cv2.imread(str(img_path))
    if img is None:
        return 0
    H, W = img.shape[:2]

    has_labels = lbl_path and lbl_path.exists()
    has_masks = mask_path and mask_path.exists()

    mask_img = None
    if has_masks:
        mask_img = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    yolo_polys = _process_yolo_labels(lbl_path, W, H) if has_labels else []
    tile_boxes = _generate_tile_boxes(W, H, tile_size, overlap)

    stem = img_path.stem
    tiles_saved = 0

    for i, (x1, y1, x2, y2) in enumerate(tile_boxes):
        tile_w = x2 - x1
        tile_h = y2 - y1
        if tile_w <= 0 or tile_h <= 0:
            continue

        tile_box = box(x1, y1, x2, y2)
        tile_img = img[y1:y2, x1:x2]

        # 1. Handle Semantic Masks (Stage 1 SOD edge case preservation)
        if has_masks and mask_img is not None:
            tile_mask = mask_img[y1:y2, x1:x2]
            cv2.imwrite(str(out_mask_dir / f"{stem}_t{i}.png"), tile_mask)

        # 2. Handle YOLO Labels (Stage 2/3 Shapely clipping)
        if has_labels:
            new_labels = []
            for cls_id, poly in yolo_polys:
                clipped = poly.intersection(tile_box)
                if clipped.is_empty:
                    continue

                polys_to_process = (
                    list(clipped.geoms)
                    if isinstance(clipped, MultiPolygon)
                    else [clipped]
                )

                for p in polys_to_process:
                    # Skip tiny fragments caused by clipping
                    if poly.area > 10 and p.area < (poly.area * min_area_ratio):
                        continue

                    coords = []
                    for px, py in p.exterior.coords[:-1]:
                        nx = max(0.0, min(1.0, (px - x1) / tile_w))
                        ny = max(0.0, min(1.0, (py - y1) / tile_h))
                        coords.extend([nx, ny])

                    if len(coords) >= 6:
                        coord_str = " ".join(f"{c:.6f}" for c in coords)
                        new_labels.append(f"{cls_id} {coord_str}")

            with open(out_lbl_dir / f"{stem}_t{i}.txt", "w") as f:
                f.write("\n".join(new_labels))

        # Save tile image
        cv2.imwrite(str(out_img_dir / f"{stem}_t{i}.jpg"), tile_img)
        tiles_saved += 1

    return tiles_saved


def tile_dataset(
    original_id: str, new_id: str, tile_size: int, overlap: float, min_area_ratio: float
) -> dict:
    """Create a tiled version of a dataset."""
    src_root = DATA_PROCESSED_DIR / original_id
    dest_root = DATA_PROCESSED_DIR / new_id

    if not src_root.exists():
        raise ValueError(f"Source dataset '{original_id}' not found.")
    if dest_root.exists():
        raise ValueError(f"Destination dataset '{new_id}' already exists.")

    dest_root.mkdir(parents=True)
    total_tiles = 0

    # Discover splits (train, val, test)
    splits = []
    for split in ("train", "val", "test"):
        if (src_root / "images" / split).exists():
            splits.append(split)

    if not splits and (src_root / "images").exists():
        splits.append("all")  # Unsplit fallback

    for split in splits:
        img_dir = src_root / "images" / split
        lbl_dir = src_root / "labels" / split
        mask_dir = src_root / "masks" / split

        out_img_dir = dest_root / "images" / split
        out_lbl_dir = dest_root / "labels" / split
        out_mask_dir = dest_root / "masks" / split

        out_img_dir.mkdir(parents=True, exist_ok=True)
        if lbl_dir.exists():
            out_lbl_dir.mkdir(parents=True, exist_ok=True)
        if mask_dir.exists():
            out_mask_dir.mkdir(parents=True, exist_ok=True)

        for img_path in img_dir.iterdir():
            if img_path.is_file() and img_path.suffix.lower() in IMAGE_EXTENSIONS:
                lbl_path = (
                    lbl_dir / f"{img_path.stem}.txt" if lbl_dir.exists() else None
                )
                # Check for .png mask with same stem
                mask_path = None
                if mask_dir.exists():
                    for ext in [".png", ".jpg", ".jpeg"]:
                        candidate = mask_dir / f"{img_path.stem}{ext}"
                        if candidate.exists():
                            mask_path = candidate
                            break

                total_tiles += _tile_single_image(
                    img_path,
                    lbl_path,
                    mask_path,
                    out_img_dir,
                    out_lbl_dir,
                    out_mask_dir,
                    tile_size,
                    overlap,
                    min_area_ratio,
                )

    # Copy/Update data.yaml
    src_yaml = src_root / "data.yaml"
    if not src_yaml.exists():
        src_yaml = src_root / "dataset.yaml"

    if src_yaml.exists():
        with open(src_yaml, "r") as f:
            yaml_data = yaml.safe_load(f) or {}
        yaml_data["path"] = str(dest_root.resolve())
        for split in splits:
            yaml_data[split] = f"images/{split}"

        # If it has masks, ensure masks_dir is set
        if (dest_root / "masks").exists():
            yaml_data["masks_dir"] = "masks"

        with open(dest_root / "data.yaml", "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    return {
        "success": True,
        "original_dataset_id": original_id,
        "new_dataset_id": new_id,
        "tiles_generated": total_tiles,
        "message": f"Tiled '{original_id}' into '{new_id}' ({total_tiles} tiles created).",
    }
