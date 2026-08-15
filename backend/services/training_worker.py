"""Background training worker.
Dispatches unified LaunchRequests to stage-specific train.py scripts,
merges config overrides, snapshots the final YAML, and streams logs.
"""

import logging
import os
import subprocess
import sys
import threading
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict

from core.config import settings
from schemas.training import JobStatus, LaunchRequest, StageType, TrainingJob
from services.training_db import training_db

logger = logging.getLogger(__name__)

PROJECT_ROOT = settings.workspace_root
LOGS_DIR = PROJECT_ROOT / "backend" / "data" / "logs" / "training"
CONFIGS_DIR = PROJECT_ROOT / "backend" / "data" / "configs" / "training"

# Map stage to the exact trainer script relative to PROJECT_ROOT
TRAINER_SCRIPTS = {
    StageType.STAGE1: "src/stage1/train/train.py",
    StageType.STAGE2: "src/stage2/train/train.py",
    StageType.STAGE3: "src/stage3/train/train.py",
}

LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)


def deep_merge(d: dict, u: dict) -> dict:
    """Deep merge two dictionaries. u overrides d."""
    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            d[k] = deep_merge(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def _build_merged_config(job: TrainingJob) -> Path:
    """Load base config, apply overrides, inject job metadata, and save snapshot."""
    merged_config = {}

    if job.config_path:
        base_path = PROJECT_ROOT / job.config_path
        if base_path.exists():
            with open(base_path, "r") as f:
                merged_config = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Base config not found at {base_path}, starting empty.")

    # Apply UI overrides
    if job.overrides:
        merged_config = deep_merge(merged_config, job.overrides)

    # Inject job-specific metadata (handles both flat Stage 2/3 and nested Stage 1 schemas)
    merged_config["project_name"] = job.project_name
    merged_config["run_name"] = job.run_name

    if job.stage == StageType.STAGE1:
        if "logging" not in merged_config:
            merged_config["logging"] = {}
        merged_config["logging"]["experiment_name"] = job.project_name
        merged_config["logging"]["run_name"] = job.run_name
        if "project" not in merged_config:
            merged_config["project"] = {}
        merged_config["project"]["name"] = job.project_name
        merged_config["project"]["run_name"] = job.run_name

    if job.base_model:
        if job.stage == StageType.STAGE1:
            if "model" not in merged_config:
                merged_config["model"] = {}
            merged_config["model"]["preset"] = job.base_model
        else:
            merged_config["model_preset"] = job.base_model

    out_path = CONFIGS_DIR / f"{job.id}.yaml"
    with open(out_path, "w") as f:
        yaml.dump(merged_config, f, default_flow_style=False, sort_keys=False)

    return out_path


class TrainingWorker:
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def _run_job(self, job: TrainingJob):
        """Execute the training job in a subprocess."""
        try:
            training_db.update_job_status(
                job.id, JobStatus.RUNNING, started_at=datetime.utcnow().isoformat()
            )

            log_path = Path(job.log_file)
            merged_config_path = _build_merged_config(job)

            trainer_rel = TRAINER_SCRIPTS.get(job.stage)
            if not trainer_rel:
                raise ValueError(f"No trainer script defined for {job.stage}")

            trainer_path = PROJECT_ROOT / trainer_rel
            if not trainer_path.exists():
                raise FileNotFoundError(f"Trainer script not found: {trainer_path}")

            # Use current python executable (conda env) unless overridden
            python_exe = os.environ.get("TRAINING_PYTHON_PATH", sys.executable)

            cmd = [
                python_exe,
                str(trainer_path),
                "--config",
                str(merged_config_path),
                "--data",
                str(job.dataset_path),
            ]

            env = os.environ.copy()
            # Ensure src/ is in PYTHONPATH so `from stage1...` imports work
            src_path = str(PROJECT_ROOT / "src")
            env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

            logger.info(f"Launching training job {job.id}: {' '.join(cmd)}")

            with open(log_path, "w") as log_file:
                process = subprocess.Popen(
                    cmd,
                    cwd=str(PROJECT_ROOT),
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                self.active_processes[job.id] = process
                process.wait()

            if process.returncode == 0:
                training_db.update_job_status(
                    job.id,
                    JobStatus.COMPLETED,
                    completed_at=datetime.utcnow().isoformat(),
                )
            else:
                training_db.update_job_status(
                    job.id,
                    JobStatus.FAILED,
                    error_message=f"Process exited with code {process.returncode}",
                    completed_at=datetime.utcnow().isoformat(),
                )

        except Exception as e:
            logger.exception(f"Job {job.id} failed")
            training_db.update_job_status(
                job.id,
                JobStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow().isoformat(),
            )
        finally:
            self.active_processes.pop(job.id, None)

    def launch(self, request: LaunchRequest) -> TrainingJob:
        """Queue and start a new training job."""
        job = TrainingJob(
            stage=request.stage,
            dataset_path=request.dataset_path,
            config_path=request.config_path,
            base_model=request.base_model,
            device=request.device,
            project_name=request.project_name or f"{request.stage.value}_exp",
            run_name=request.run_name
            or f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            overrides=request.overrides,
        )
        job.log_file = str(LOGS_DIR / f"{job.id}.log")

        training_db.insert_job(job)

        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()

        return job

    def stop_job(self, job_id: str) -> bool:
        """Terminate a running training job."""
        proc = self.active_processes.get(job_id)
        if proc and proc.poll() is None:
            proc.terminate()
            training_db.update_job_status(
                job_id, JobStatus.CANCELLED, completed_at=datetime.utcnow().isoformat()
            )
            return True
        return False


worker = TrainingWorker()
