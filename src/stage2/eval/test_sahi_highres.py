import argparse
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
from sahi.utils.cv import visualize_object_predictions
from ultralytics import YOLO

CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_component",
    5: "missing_component",
    6: "corrosion",
}


def run_direct_1024(model, img_path, device, min_conf, save_dir):
    start_time = time.time()
    results = model.predict(
        source=str(img_path),
        imgsz=1024,
        verbose=False,
        conf=min_conf,
        device=device,
    )
    latency = (time.time() - start_time) * 1000  # ms
    result = results[0]

    counts = {cid: 0 for cid in CLASS_NAMES.keys()}
    if result.boxes is not None and len(result.boxes) > 0:
        for cls_tensor in result.boxes.cls:
            cid = int(cls_tensor.item())
            if cid in counts:
                counts[cid] += 1

    # Save annotated image
    out_file = save_dir / f"{img_path.stem}_direct1024.jpg"
    result.save(filename=str(out_file))

    return counts, latency


def run_sahi_sliced(
    detection_model, img_path, slice_size, overlap_ratio, min_conf, save_dir, mode_name
):
    start_time = time.time()
    sahi_result = get_sliced_prediction(
        image=str(img_path),
        detection_model=detection_model,
        slice_height=slice_size,
        slice_width=slice_size,
        overlap_height_ratio=overlap_ratio,
        overlap_width_ratio=overlap_ratio,
        postprocess_type="NMS",
        postprocess_match_metric="IOS",
        postprocess_match_threshold=0.50,
        verbose=False,
    )
    latency = (time.time() - start_time) * 1000  # ms

    counts = {cid: 0 for cid in CLASS_NAMES.keys()}
    for obj in sahi_result.object_prediction_list:
        cid = obj.category.id
        if cid in counts:
            counts[cid] += 1

    # Save annotated visual output
    out_file = save_dir / f"{img_path.stem}_{mode_name}.jpg"
    visualization = visualize_object_predictions(
        image=np.array(Image.open(img_path)),
        object_prediction_list=sahi_result.object_prediction_list,
        rect_th=2,
        text_size=0.6,
        text_th=2,
    )
    cv2.imwrite(str(out_file), cv2.cvtColor(visualization["image"], cv2.COLOR_RGB2BGR))

    return counts, latency


def main():
    parser = argparse.ArgumentParser(
        description="High-Res SAHI 1024 vs 640 Visual Diagnostic Engine"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to trained .pt model"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="data/calibration/SAHI testing",
        help="Path to folder with high-res test images",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="runs/sahi_highres_viz",
        help="Directory to save visual comparison images",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="mps",
        help="Device for inference ('mps', 'cuda', 'cpu')",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for predictions",
    )
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    save_dir = Path(args.output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp",
        "*.avif",
        "*.JPEG",
        "*.JPG",
    ]
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(input_path.glob(ext)))

    print(f"[*] Found {len(image_files)} high-res test images in '{args.input_dir}'")
    print(f"[*] Visual annotations will be saved to '{save_dir}'")
    print(f"[*] Loading models on device '{args.device}' (conf={args.conf})...")

    direct_model = YOLO(args.model)
    sahi_model = AutoDetectionModel.from_pretrained(
        model_type="yolov8",
        model_path=args.model,
        confidence_threshold=args.conf,
        device=args.device,
    )

    totals = {
        "Direct 1024": {cid: 0 for cid in CLASS_NAMES.keys()},
        "SAHI 640": {cid: 0 for cid in CLASS_NAMES.keys()},
        "SAHI 1024": {cid: 0 for cid in CLASS_NAMES.keys()},
    }
    latencies = {"Direct 1024": [], "SAHI 640": [], "SAHI 1024": []}

    print("\n" + "=" * 105)
    print(" 🚀 RUNNING INFERENCE AND GENERATING VISUALIZATIONS")
    print("=" * 105)

    for img_path in sorted(image_files):
        try:
            with Image.open(img_path) as img:
                w, h = img.size
        except Exception:
            continue

        # 1. Direct 1024
        d1024_counts, d1024_lat = run_direct_1024(
            direct_model, img_path, args.device, args.conf, save_dir
        )
        latencies["Direct 1024"].append(d1024_lat)

        # 2. SAHI 640
        s640_counts, s640_lat = run_sahi_sliced(
            sahi_model, img_path, 640, 0.25, args.conf, save_dir, "sahi640"
        )
        latencies["SAHI 640"].append(s640_lat)

        # 3. SAHI 1024
        s1024_counts, s1024_lat = run_sahi_sliced(
            sahi_model, img_path, 1024, 0.25, args.conf, save_dir, "sahi1024"
        )
        latencies["SAHI 1024"].append(s1024_lat)

        for cid in CLASS_NAMES.keys():
            totals["Direct 1024"][cid] += d1024_counts[cid]
            totals["SAHI 640"][cid] += s640_counts[cid]
            totals["SAHI 1024"][cid] += s1024_counts[cid]

        print(f"📸 Processed: {img_path.name} ({w}x{h} px) -> Saved visualizations")

    print("\n" + "=" * 105)
    print(" 📊 AGGREGATE SUMMARY")
    print("=" * 105)
    header = (
        f"{'Mode':<15} | "
        + " | ".join([f"{CLASS_NAMES[i]:<12}" for i in sorted(CLASS_NAMES.keys())])
        + " | Total | Avg Latency"
    )
    print(header)
    print("-" * 105)

    for mode in ["Direct 1024", "SAHI 640", "SAHI 1024"]:
        row_str = f"{mode:<15} | "
        mode_counts = totals[mode]
        for cid in sorted(CLASS_NAMES.keys()):
            row_str += f"{mode_counts[cid]:<12} | "

        total_dets = sum(mode_counts.values())
        avg_lat = np.mean(latencies[mode]) if latencies[mode] else 0.0
        row_str += f"{total_dets:<5} | {avg_lat:>6.1f} ms"
        print(row_str)

    print("=" * 105)


if __name__ == "__main__":
    main()
