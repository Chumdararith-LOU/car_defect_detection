import cv2
import random
import numpy as np
from pathlib import Path


def copy_paste_augmentation(
    dataset_dir, target_classes, class_names, target_count=5000
):
    images_dir = Path(dataset_dir) / "train" / "images"
    labels_dir = Path(dataset_dir) / "train" / "labels"

    if not images_dir.exists() or not labels_dir.exists():
        print(f"[!] Error: Cannot find {images_dir} or {labels_dir}")
        return

    label_files = list(labels_dir.glob("*.txt"))
    image_files = {p.stem: p for p in images_dir.glob("*.*")}

    print("[+] Harvesting existing target polygons...")
    instances = {cls: [] for cls in target_classes}

    for label_path in label_files:
        with open(label_path, "r") as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue

            cls_id = int(parts[0])
            if cls_id in target_classes:
                coords = [float(x) for x in parts[1:]]
                instances[cls_id].append(
                    {
                        "label_path": label_path,
                        "img_path": image_files.get(label_path.stem),
                        "coords": coords,
                    }
                )

    for cls_id in target_classes:
        current_count = len(instances[cls_id])
        needed = target_count - current_count

        if needed <= 0:
            print(
                f"[✓] {class_names[cls_id]} already has {current_count} instances. Skipping."
            )
            continue

        print(
            f"[*] Augmenting {class_names[cls_id]}... Current: {current_count} | Target: {target_count} | Needed: {needed}"
        )

        source_pool = instances[cls_id]
        if not source_pool:
            print(f"[-] No instances found for {class_names[cls_id]} to copy from!")
            continue

        for i in range(needed):
            src_info = random.choice(source_pool)
            if src_info["img_path"] is None:
                continue

            src_img = cv2.imread(str(src_info["img_path"]))
            if src_img is None:
                continue

            h, w = src_img.shape[:2]

            pts = np.array(src_info["coords"]).reshape(-1, 2)
            pixel_pts = (pts * [w, h]).astype(np.int32)

            x, y, bw, bh = cv2.boundingRect(pixel_pts)

            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w, x + bw)
            y2 = min(h, y + bh)

            bw_clamped = x2 - x1
            bh_clamped = y2 - y1

            if bw_clamped <= 1 or bh_clamped <= 1:
                continue

            patch = src_img[y1:y2, x1:x2].copy()
            patch_mask = np.zeros((bh_clamped, bw_clamped), dtype=np.uint8)

            local_pts = pixel_pts - [x1, y1]
            cv2.fillPoly(patch_mask, [local_pts], 255)

            dst_label_path = random.choice(label_files)
            dst_img_path = image_files.get(dst_label_path.stem)

            if dst_img_path is None:
                continue

            dst_img = cv2.imread(str(dst_img_path))
            if dst_img is None:
                continue

            dh, dw = dst_img.shape[:2]

            if dw <= bw_clamped or dh <= bh_clamped:
                continue

            paste_x = random.randint(0, dw - bw_clamped)
            paste_y = random.randint(0, dh - bh_clamped)

            roi = dst_img[
                paste_y : paste_y + bh_clamped, paste_x : paste_x + bw_clamped
            ]

            roi[patch_mask == 255] = patch[patch_mask == 255]
            dst_img[paste_y : paste_y + bh_clamped, paste_x : paste_x + bw_clamped] = (
                roi
            )

            cv2.imwrite(str(dst_img_path), dst_img)

            new_pixel_pts = local_pts + [paste_x, paste_y]
            new_normalized = new_pixel_pts.astype(np.float32) / [dw, dh]
            new_normalized = np.clip(new_normalized, 0.0, 1.0)

            new_line = (
                f"{cls_id} "
                + " ".join([f"{coord:.6f}" for coord in new_normalized.flatten()])
                + "\n"
            )
            with open(dst_label_path, "a") as f:
                f.write(new_line)

            if (i + 1) % 500 == 0:
                print(
                    f"    -> Generated {i + 1}/{needed} {class_names[cls_id]} polygons"
                )

    print("[✓] Copy-paste augmentation complete!")


if __name__ == "__main__":
    target_dataset = "data/processed/stage2_custom"

    aug_targets = [2, 3]
    class_map = {2: "crack", 3: "glass_shatter"}

    copy_paste_augmentation(target_dataset, aug_targets, class_map, target_count=5000)
