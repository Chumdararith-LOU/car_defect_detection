import argparse
import sys
from pathlib import Path

YAML_NAME = "car_damages_panel.yaml"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite only the 'path:' line inside a YOLO dataset YAML so the "
            "dataset is portable between the MacBook and the training server. "
            "All other lines (class names, train/val/test entries) are preserved."
        )
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        required=True,
        help=(
            f"Directory containing {YAML_NAME}; its absolute path becomes the "
            "new 'path:' value"
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()

    if not dataset_dir.is_dir():
        print(f"ERROR: dataset directory not found: {dataset_dir}", file=sys.stderr)
        sys.exit(1)

    yaml_path = dataset_dir / YAML_NAME

    if not yaml_path.is_file():
        print(f"ERROR: dataset YAML not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    with open(yaml_path, "r") as f:
        lines = f.read().splitlines()

    replaced = False

    for i, line in enumerate(lines):
        if line.startswith("path:"):
            lines[i] = f"path: {dataset_dir.as_posix()}"
            replaced = True
            break

    if not replaced:
        print(
            f"ERROR: no 'path:' line found in {yaml_path}; refusing to modify.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(yaml_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Updated dataset YAML: {yaml_path}")
    print(f"path: {dataset_dir.as_posix()}")


if __name__ == "__main__":
    main()
