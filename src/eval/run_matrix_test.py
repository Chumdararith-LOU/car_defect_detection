import yaml
import subprocess
from pathlib import Path


def main():
    matrix_path = Path("configs/data/matrix_test.yaml")
    base_config_path = Path("configs/pipeline_config.yaml")

    with open(matrix_path, "r") as f:
        matrix_data = yaml.safe_load(f)

    with open(base_config_path, "r") as f:
        pipe_cfg = yaml.safe_load(f)

    print(
        f"  Initializing Bulk Evaluation Engine for {len(matrix_data['models'])} variants..."
    )

    for model_info in matrix_data["models"]:
        print("\n" + "=" * 80)
        print(f"Evaluating Model Node: {model_info['id']}")
        print(f"Path: {model_info['path']}")
        print("=" * 80)

        pipe_cfg["hardware"]["device"] = "cuda:0"
        pipe_cfg["dataset"]["imgsz"] = model_info["imgsz"]

        if model_info["tiled"]:
            pipe_cfg["gating_thresholds"]["pixel_thresh_high"] = (
                0.47 if "yolo26n" in model_info["id"] else 0.28
            )
            pipe_cfg["gating_thresholds"]["pixel_thresh_low"] = (
                0.35 if "yolo26n" in model_info["id"] else 0.18
            )
        else:
            pipe_cfg["gating_thresholds"]["pixel_thresh"] = 0.70

        temp_config = Path("configs/temp_matrix_config.yaml")
        with open(temp_config, "w") as f:
            yaml.dump(pipe_cfg, f)

        cmd = [
            "python",
            "src/eval/evaluate_test.py",
            "--config",
            str(temp_config),
            "--model_path",
            model_info["path"],
        ]

        try:
            subprocess.run(cmd, check=True, env={"PYTHONPATH": ".", **os.environ})
        except Exception as e:
            print(
                f" Verification failed for model execution block {model_info['id']}: {e}"
            )

        if temp_config.exists():
            temp_config.unlink()


if __name__ == "__main__":
    import os

    main()
