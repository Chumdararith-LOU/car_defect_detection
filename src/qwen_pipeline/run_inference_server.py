import json
import argparse
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

# Config
PROMPT_FILE = Path(__file__).parent / "qwen_system_prompt.txt"
PRELABELS_DIR = Path("../../data/qwen_staging")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Qwen2.5-VL inference on batch manifests"
    )
    parser.add_argument(
        "--batch", type=str, required=True, help="Batch folder name (e.g., batch_001)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-VL-7B-Instruct",
        help="HuggingFace model path",
    )
    return parser.parse_args()


def load_system_prompt():
    with open(PROMPT_FILE, "r") as f:
        return f.read().strip()


def main():
    args = parse_args()
    batch_dir = PRELABELS_DIR / args.batch
    manifest_path = batch_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"[!] Manifest not found at: {manifest_path}")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    outputs_dir = batch_dir / "qwen_outputs"
    failed_dir = batch_dir / "failed"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    error_log_path = batch_dir / "errors.log"

    system_prompt = load_system_prompt()

    print(f"[*] Loading Model {args.model} onto RTX 3090...")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    processor = AutoProcessor.from_pretrained(args.model)

    print(f"[*] Processing {len(manifest['images'])} images in {args.batch}...")

    coco_annotations = []
    coco_images = []
    ann_id_counter = 1

    # Class Mapping to ID 1..9
    class_map = {
        "dent": 1,
        "ding": 2,
        "deform": 3,
        "scratch_hairline": 4,
        "scratch_gouge": 5,
        "crack": 6,
        "glass_shatter": 7,
        "broken_component": 8,
        "corrosion": 9,
    }

    for img_idx, img_entry in enumerate(manifest["images"], start=1):
        img_id = img_entry["id"]
        img_path = Path(
            img_entry.get("abs_path") or (batch_dir / img_entry["filename"])
        )

        if not img_path.exists():
            print(f"[-] Missing image: {img_path}")
            continue

        try:
            image = Image.open(img_path).convert("RGB")
            img_w, img_h = image.size

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(img_path)},
                        {"type": "text", "text": system_prompt},
                    ],
                }
            ]

            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = processor(
                text=[text], images=[image], padding=True, return_tensors="pt"
            ).to("cuda")

            with torch.no_grad():
                generated_ids = model.generate(**inputs, max_new_tokens=512)

            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            response_text = processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            # Try parsing output JSON
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            parsed_detections = json.loads(clean_text)

            # Save raw image JSON
            out_json = outputs_dir / f"{img_path.stem}.json"
            with open(out_json, "w") as f:
                json.dump(parsed_detections, f, indent=4)

            # Build COCO format
            coco_images.append(
                {
                    "id": img_idx,
                    "file_name": img_path.name,
                    "width": img_w,
                    "height": img_h,
                }
            )

            for det in parsed_detections:
                cls_name = det.get("class_name")
                if cls_name not in class_map:
                    continue

                x1, y1, x2, y2 = det["bbox"]
                # Convert normalized [x1, y1, x2, y2] to COCO [x, y, w, h] absolute pixels
                abs_x = x1 * img_w
                abs_y = y1 * img_h
                abs_w = (x2 - x1) * img_w
                abs_h = (y2 - y1) * img_h

                coco_annotations.append(
                    {
                        "id": ann_id_counter,
                        "image_id": img_idx,
                        "category_id": class_map[cls_name],
                        "bbox": [
                            round(abs_x, 2),
                            round(abs_y, 2),
                            round(abs_w, 2),
                            round(abs_h, 2),
                        ],
                        "area": round(abs_w * abs_h, 2),
                        "iscrowd": 0,
                        "score": det.get("confidence", 1.0),
                    }
                )
                ann_id_counter += 1

        except Exception as e:
            print(f"[!] Error on {img_path.name}: {e}")
            with open(error_log_path, "a") as f_err:
                f_err.write(f"{img_path.name}: {str(e)}\n")

            with open(failed_dir / f"{img_path.stem}_failed.txt", "w") as f_fail:
                f_fail.write(response_text if "response_text" in locals() else str(e))

    # Write CVAT COCO JSON
    cvat_dir = batch_dir / "cvat_import"
    cvat_dir.mkdir(parents=True, exist_ok=True)

    coco_dataset = {
        "images": coco_images,
        "annotations": coco_annotations,
        "categories": [{"id": v, "name": k} for k, v in class_map.items()],
    }

    with open(cvat_dir / "annotations.json", "w") as f:
        json.dump(coco_dataset, f, indent=4)

    print(f"[✓] Inference complete for {args.batch}!")
    print(f"[✓] CVAT import ready at: {cvat_dir / 'annotations.json'}")


if __name__ == "__main__":
    main()
