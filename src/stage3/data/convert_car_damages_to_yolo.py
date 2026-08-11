import argparse
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import cv2
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, box


def sanitize_stem(stem: str, fallback: str) -> str:
    """Sanitize a filename stem for safer YOLO dataset paths."""
    stem = stem.strip()

    if not stem:
        return fallback

    stem = stem.replace(" ", "_")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem)
    stem = stem.strip("._")

    if not stem:
        return fallback

    return stem


def load_classes(meta_path: Path):
    """Load official class names and IDs from meta.json."""
    with open(meta_path, "r") as f:
        meta = json.load(f)

    classes = meta.get("classes")

    if not isinstance(classes, list) or len(classes) == 0:
        raise ValueError(f"Could not find a valid classes list in {meta_path}")

    names = []
    class_id_to_idx = {}
    title_to_idx = {}

    for idx, item in enumerate(classes):
        title = item.get("title")

        if not title:
            raise ValueError(f"Class at index {idx} in {meta_path} has no title.")

        names.append(title)

        if "id" in item:
            class_id_to_idx[item["id"]] = idx

        title_to_idx[title] = idx

    return names, class_id_to_idx, title_to_idx


def ensure_empty_dir(path: Path, overwrite: bool):
    """Ensure output directory is empty or create it."""
    if path.exists():
        if not overwrite:
            raise RuntimeError(
                f"Output directory already exists: {path}. "
                "Pass --overwrite if you want to replace it."
            )

        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    path.mkdir(parents=True, exist_ok=True)


def clean_ring(ring, width, height):
    """Clip ring coordinates to image bounds."""
    points = []

    for point in ring:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue

        x = float(point[0])
        y = float(point[1])

        x = max(0.0, min(float(width), x))
        y = max(0.0, min(float(height), y))

        points.append((x, y))

    return points


def geometry_to_polygons(exterior, interior, width, height, report):
    """Convert one annotation object to one or more Shapely polygons.

    Interior holes are subtracted from the exterior polygon.
    """
    if len(exterior) < 3:
        report["skipped_exterior_too_small"] += 1
        return []

    exterior_pts = clean_ring(exterior, width, height)

    if len(exterior_pts) < 3:
        report["skipped_exterior_too_small"] += 1
        return []

    try:
        result = Polygon(exterior_pts)

        if not result.is_valid:
            result = result.buffer(0)

    except Exception:
        report["skipped_invalid_exterior"] += 1
        return []

    image_box = box(0, 0, width, height)

    if interior:
        report["input_polygons_with_holes"] += 1

        for hole_ring in interior:
            if len(hole_ring) < 3:
                report["skipped_invalid_hole"] += 1
                continue

            hole_pts = clean_ring(hole_ring, width, height)

            if len(hole_pts) < 3:
                report["skipped_invalid_hole"] += 1
                continue

            try:
                hole = Polygon(hole_pts)

                if not hole.is_valid:
                    hole = hole.buffer(0)

                result = result.difference(hole)

                if not result.is_valid:
                    result = result.buffer(0)

            except Exception:
                report["skipped_failed_hole_difference"] += 1
                continue

    try:
        result = result.intersection(image_box)

        if not result.is_valid:
            result = result.buffer(0)

    except Exception:
        report["skipped_failed_clip"] += 1
        return []

    if result.is_empty:
        report["skipped_empty_after_processing"] += 1
        return []

    polygons = []

    if isinstance(result, Polygon):
        polygons.append(result)

    elif isinstance(result, MultiPolygon):
        polygons.extend(result.geoms)

    elif isinstance(result, GeometryCollection):
        for geom in result.geoms:
            if isinstance(geom, Polygon):
                polygons.append(geom)

    else:
        report["skipped_unsupported_geometry"] += 1
        return []

    return polygons


def polygon_to_yolo_line(class_idx, polygon, width, height, min_area_px):
    """Convert a Shapely polygon to one YOLO segmentation label line."""
    if polygon.area < min_area_px:
        return None, "small"

    exterior = list(polygon.exterior.coords)

    if len(exterior) > 1 and exterior[0] == exterior[-1]:
        exterior = exterior[:-1]

    if len(exterior) < 3:
        return None, "too_few_points"

    coords = []

    for x, y in exterior:
        xn = max(0.0, min(1.0, x / float(width)))
        yn = max(0.0, min(1.0, y / float(height)))

        coords.append(f"{xn:.6f}")
        coords.append(f"{yn:.6f}")

    line = " ".join([str(class_idx)] + coords)

    return line, "ok"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Convert Dataset A (Car damages, Supervisely-style JSON polygons) "
            "into a YOLO segmentation dataset for Stage 3 panel segmentation."
        )
    )
    parser.add_argument(
        "--raw-root",
        type=str,
        default="data/raw/archive/Car damages dataset",
        help="Root directory of the raw Car damages dataset",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="data/processed/stage3/car_damages_panel",
        help="Output directory for the converted YOLO dataset",
    )
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-area-px", type=float, default=25.0)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If greater than 0, convert only the first N annotation files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output directory if it already exists",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    raw_root = Path(args.raw_root)
    out_dir = Path(args.out_dir)
    seed = args.seed
    train_ratio = args.train_ratio
    val_ratio = args.val_ratio
    test_ratio = args.test_ratio
    min_area_px = args.min_area_px
    limit = args.limit
    overwrite = args.overwrite

    assert (
        abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
    ), "Split ratios must sum to 1.0."

    file1_dir = raw_root / "File1"
    ann_dir = file1_dir / "ann"
    img_dir = file1_dir / "img"
    meta_path = raw_root / "meta.json"

    assert ann_dir.exists(), f"Annotation directory not found: {ann_dir}"
    assert img_dir.exists(), f"Image directory not found: {img_dir}"
    assert meta_path.exists(), f"meta.json not found: {meta_path}"

    names, class_id_to_idx, title_to_idx = load_classes(meta_path)

    print(f"Loaded {len(names)} classes from meta.json:")
    for idx, name in enumerate(names):
        print(f"{idx:>2}: {name}")

    ensure_empty_dir(out_dir, overwrite)

    for split in ["train", "val", "test"]:
        (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    ann_files = sorted(ann_dir.glob("*.json"))

    if limit > 0:
        ann_files = ann_files[:limit]

    n_total = len(ann_files)

    assert n_total > 0, "No annotation files found."

    n_test = int(round(n_total * test_ratio))
    n_val = int(round(n_total * val_ratio))
    n_train = n_total - n_val - n_test

    assert n_train >= 0, "Invalid split counts."

    file_order = [p.name[:-5] for p in ann_files]
    rng = random.Random(seed)
    rng.shuffle(file_order)

    train_set = set(file_order[:n_train])
    val_set = set(file_order[n_train : n_train + n_val])
    test_set = set(file_order[n_train + n_val :])

    print()
    print("Dataset split prepared.")
    print(f"Output directory: {out_dir}")
    print(f"Total images: {n_total}")
    print(f"Train: {len(train_set)}")
    print(f"Val:   {len(val_set)}")
    print(f"Test:  {len(test_set)}")

    report = {
        "source_root": str(raw_root),
        "output_dir": str(out_dir),
        "seed": seed,
        "split_ratios": {
            "train": train_ratio,
            "val": val_ratio,
            "test": test_ratio,
        },
        "num_images_total": n_total,
        "split_counts": {
            "train": len(train_set),
            "val": len(val_set),
            "test": len(test_set),
        },
        "class_names": names,
        "images_written": 0,
        "labels_written": 0,
        "input_polygons": 0,
        "output_yolo_polygons": 0,
        "input_polygons_with_holes": 0,
        "output_polygon_counts_by_class": Counter(),
        "missing_images": [],
        "image_read_failures": [],
        "size_mismatches": [],
        "unknown_classes": Counter(),
        "filename_collisions": [],
        "skipped_non_polygon_objects": 0,
        "skipped_unknown_class": 0,
        "skipped_exterior_too_small": 0,
        "skipped_invalid_exterior": 0,
        "skipped_invalid_hole": 0,
        "skipped_failed_hole_difference": 0,
        "skipped_failed_clip": 0,
        "skipped_empty_after_processing": 0,
        "skipped_unsupported_geometry": 0,
        "skipped_small_polygons": 0,
        "skipped_too_few_points": 0,
    }

    used_output_names = {}

    for idx, ann_file in enumerate(ann_files):
        # Example: "Car damages 100.png.json" -> "Car damages 100.png"
        image_name = ann_file.name[:-5]

        image_path = img_dir / image_name

        if image_name in train_set:
            split = "train"
        elif image_name in val_set:
            split = "val"
        elif image_name in test_set:
            split = "test"
        else:
            raise RuntimeError(f"Could not assign split for: {image_name}")

        if not image_path.exists():
            report["missing_images"].append(image_name)
            continue

        img = cv2.imread(str(image_path))

        if img is None:
            report["image_read_failures"].append(image_name)
            continue

        actual_height, actual_width = img.shape[:2]

        with open(ann_file, "r") as f:
            ann = json.load(f)

        json_size = ann.get("size", {})
        json_height = json_size.get("height")
        json_width = json_size.get("width")

        if (json_height, json_width) != (actual_height, actual_width):
            report["size_mismatches"].append(
                {
                    "image": image_name,
                    "json_size": [json_height, json_width],
                    "actual_size": [actual_height, actual_width],
                }
            )

        width = actual_width
        height = actual_height

        image_path_obj = Path(image_name)
        original_stem = image_path_obj.stem
        suffix = image_path_obj.suffix.lower() or ".jpg"

        base_sanitized_stem = sanitize_stem(original_stem, f"image_{idx:06d}")
        sanitized_stem = base_sanitized_stem
        sanitized_name = f"{sanitized_stem}{suffix}"

        if sanitized_name in used_output_names:
            report["filename_collisions"].append(
                {
                    "output_name": sanitized_name,
                    "existing_image": used_output_names[sanitized_name],
                    "new_image": image_name,
                }
            )

            dup = 1

            while sanitized_name in used_output_names:
                sanitized_stem = f"{base_sanitized_stem}_dup{dup}"
                sanitized_name = f"{sanitized_stem}{suffix}"
                dup += 1

        used_output_names[sanitized_name] = image_name

        lines = []

        for obj in ann.get("objects", []):
            if obj.get("geometryType") != "polygon":
                report["skipped_non_polygon_objects"] += 1
                continue

            class_id = obj.get("classId")
            class_title = obj.get("classTitle")

            class_idx = None

            if class_id in class_id_to_idx:
                class_idx = class_id_to_idx[class_id]
            elif class_title in title_to_idx:
                class_idx = title_to_idx[class_title]
            else:
                report["skipped_unknown_class"] += 1
                report["unknown_classes"][str(class_title)] += 1
                continue

            points = obj.get("points", {})
            exterior = points.get("exterior") or []
            interior = points.get("interior") or []

            report["input_polygons"] += 1

            polygons = geometry_to_polygons(
                exterior=exterior,
                interior=interior,
                width=width,
                height=height,
                report=report,
            )

            for polygon in polygons:
                line, status = polygon_to_yolo_line(
                    class_idx=class_idx,
                    polygon=polygon,
                    width=width,
                    height=height,
                    min_area_px=min_area_px,
                )

                if status == "ok":
                    lines.append(line)
                    report["output_yolo_polygons"] += 1
                    report["output_polygon_counts_by_class"][names[class_idx]] += 1

                elif status == "small":
                    report["skipped_small_polygons"] += 1

                elif status == "too_few_points":
                    report["skipped_too_few_points"] += 1

        shutil.copy2(
            image_path,
            out_dir / "images" / split / sanitized_name,
        )
        report["images_written"] += 1

        label_path = out_dir / "labels" / split / f"{sanitized_stem}.txt"

        with open(label_path, "w") as f:
            if lines:
                f.write("\n".join(lines) + "\n")

        report["labels_written"] += 1

    print("Conversion loop finished.")
    print(f"Images written: {report['images_written']}")
    print(f"Labels written: {report['labels_written']}")
    print(f"Input polygons: {report['input_polygons']}")
    print(f"Output YOLO polygons: {report['output_yolo_polygons']}")
    print(f"Input polygons with holes: {report['input_polygons_with_holes']}")

    report["unknown_classes"] = dict(report["unknown_classes"])
    report["output_polygon_counts_by_class"] = dict(
        report["output_polygon_counts_by_class"]
    )

    yaml_lines = [
        "# Generated by src/stage3/data/convert_car_damages_to_yolo.py",
        "# Stage 3 panel/component segmentation dataset",
        f"path: {out_dir.resolve().as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        f"nc: {len(names)}",
        "names:",
    ]

    for idx, name in enumerate(names):
        yaml_lines.append(f'  {idx}: "{name}"')

    yaml_path = out_dir / "car_damages_panel.yaml"

    with open(yaml_path, "w") as f:
        f.write("\n".join(yaml_lines) + "\n")

    report_path = out_dir / "conversion_report.json"

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("Dataset YAML written:")
    print(yaml_path)
    print()
    print("Conversion report written:")
    print(report_path)

    print("=" * 70)
    print("Conversion Summary")
    print("=" * 70)

    print(f"Output directory: {out_dir}")
    print(f"Images written: {report['images_written']}")
    print(f"Labels written: {report['labels_written']}")
    print(f"Input polygons: {report['input_polygons']}")
    print(f"Output YOLO polygons: {report['output_yolo_polygons']}")
    print(f"Input polygons with holes: {report['input_polygons_with_holes']}")
    print(f"Split counts: {report['split_counts']}")

    print()
    print("Output polygon counts by class:")

    for class_name, count in sorted(
        report["output_polygon_counts_by_class"].items(),
        key=lambda item: -item[1],
    ):
        print(f"  {class_name:<20} {count}")


if __name__ == "__main__":
    main()
