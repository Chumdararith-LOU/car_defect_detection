import argparse
import yaml
import mlflow
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Automated Model Export Pipeline")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to export_config.yaml"
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)

    model = YOLO(cfg["pt_model_path"])

    for fmt in cfg["deployment_targets"]:
        print(f" Exporting to {fmt}...")

        model.export(
            format=fmt,
            int8=cfg["export_settings"]["int8"],
            data=cfg["calibration_data"],
        )

        with mlflow.start_run(run_name=f"export_{fmt}"):
            mlflow.log_param("format", fmt)
            mlflow.log_param("int8", cfg["export_settings"]["int8"])
            print(f" {fmt} export complete and registered.")


if __name__ == "__main__":
    main()
