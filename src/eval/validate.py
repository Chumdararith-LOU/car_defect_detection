import os
import argparse
import shutil
from datetime import datetime
import mlflow
from mlflow.tracking import MlflowClient
from jinja2 import Environment, FileSystemLoader


def setup_directories(run_name):
    """Creates isolated reporting directories for the specific run."""
    docs_dir = "docs/reports"
    fig_dir = f"docs/reports/figures/{run_name}"
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)
    return docs_dir, fig_dir


def fetch_mlflow_data(project_name, run_name):
    """Queries the MLflow API for agnostic run parameters and metrics."""
    client = MlflowClient()
    experiment = client.get_experiment_by_name(project_name)

    if not experiment:
        raise ValueError(f"Experiment '{project_name}' not found in MLflow.")

    # Search for the exact run name
    query = f"tags.mlflow.runName = '{run_name}'"
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id], filter_string=query
    )

    if not runs:
        raise ValueError(
            f"Run '{run_name}' not found in MLflow project '{project_name}'."
        )

    run = runs[0]
    return run.data.params, run.data.metrics, run.data.tags, run.info.run_id


def gather_artifacts(source_dir, dest_fig_dir):
    """Dynamically copies any generated .png or .jpg figures (Agnostic to YOLO)."""
    copied_figures = []
    if os.path.exists(source_dir):
        for file in os.listdir(source_dir):
            if file.endswith((".png", ".jpg", ".jpeg")):
                src_path = os.path.join(source_dir, file)
                dest_path = os.path.join(dest_fig_dir, file)
                shutil.copy(src_path, dest_path)
                copied_figures.append(file)
    return copied_figures


def render_report(template_path, output_path, data):
    """Injects MLflow data into the Jinja2 Markdown template."""
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
    template = env.get_template(os.path.basename(template_path))

    rendered_md = template.render(**data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_md)
    print(f" Automated Report successfully generated at: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Agnostic MLOps Report Generator")
    parser.add_argument(
        "--project", type=str, required=True, help="MLflow Project/Experiment Name"
    )
    parser.add_argument("--run-name", type=str, required=True, help="MLflow Run Name")
    parser.add_argument(
        "--yolo-dir",
        type=str,
        default=None,
        help="Path to raw Ultralytics output (e.g. runs/segment/run_name)",
    )
    parser.add_argument(
        "--template",
        type=str,
        default="reports/templates/experiment_report.md.j2",
        help="Path to Jinja2 template",
    )
    args = parser.parse_args()

    # 1. Bind to MLflow Server
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(mlflow_uri)

    # 2. Setup isolated paths
    docs_dir, fig_dir = setup_directories(args.run_name)
    output_md_path = os.path.join(docs_dir, f"{args.run_name}_report.md")

    print(f" Fetching telemetry for {args.project} -> {args.run_name}...")
    params, metrics, tags, run_id = fetch_mlflow_data(args.project, args.run_name)

    target_dir = (
        args.yolo_dir if args.yolo_dir else os.path.join(args.project, args.run_name)
    )

    figures = []
    if target_dir and os.path.exists(target_dir):
        print(f" Harvesting visual artifacts from {target_dir}...")
        figures = gather_artifacts(target_dir, fig_dir)

    payload = {
        "project_name": args.project,
        "run_name": args.run_name,
        "date_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "params": params,
        "metrics": metrics,
        "tags": tags,
        "figures": figures,
        "run_id": run_id,
    }

    render_report(args.template, output_md_path, payload)


if __name__ == "__main__":
    main()
