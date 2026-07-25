from pathlib import Path
import yaml


def main():
    print("[⚙] Patching dataset_6k labels for CVAT import...")

    dataset_path = Path(
        "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/dataset_6k"
    )
    labels_dir = dataset_path / "labels"
    yaml_path = dataset_path / "data.yaml"

    # The new target taxonomy
    new_classes = [
        "ding",  # 0
        "dent",  # 1 (Old dent moves here)
        "deform",  # 2
        "scratch",  # 3
        "crack",  # 4
        "glass_shatter",  # 5
        "broken_component",  # 6
        "corrosion",  # 7
    ]

    # Map old indices to new indices. (-1 means delete)
    # Old: 0:dent, 1:scratch, 2:crack, 3:glass_shatter, 4:broken_component, 5:missing_component, 6:corrosion
    index_mapping = {
        0: 1,  # dent -> dent
        1: 3,  # scratch -> scratch
        2: 4,  # crack -> crack
        3: 5,  # glass_shatter -> glass_shatter
        4: 6,  # broken_component -> broken_component
        5: -1,  # missing_component -> REMOVE
        6: 7,  # corrosion -> corrosion
    }

    files_modified = 0
    masks_deleted = 0

    # 1. Update all YOLO .txt files
    for txt_file in labels_dir.glob("*.txt"):
        with open(txt_file, "r") as f:
            lines = f.readlines()

        new_lines = []
        modified = False

        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue

            old_idx = int(parts[0])
            new_idx = index_mapping.get(old_idx, -1)

            if new_idx == -1:
                masks_deleted += 1
                modified = True
            else:
                if old_idx != new_idx:
                    parts[0] = str(new_idx)
                    modified = True
                new_lines.append(" ".join(parts) + "\n")

        if modified:
            with open(txt_file, "w") as f:
                f.writelines(new_lines)
            files_modified += 1

    # 2. Update data.yaml
    with open(yaml_path, "r") as f:
        yaml_data = yaml.safe_load(f)

    yaml_data["names"] = {idx: name for idx, name in enumerate(new_classes)}

    with open(yaml_path, "w") as f:
        yaml.safe_dump(yaml_data, f, default_flow_style=False)

    print(f"[✓] Successfully updated {files_modified} label files.")
    print(f"[✓] Permanently removed {masks_deleted} 'missing_component' instances.")
    print("[✓] data.yaml updated with the new 8-class taxonomy.")


if __name__ == "__main__":
    main()
