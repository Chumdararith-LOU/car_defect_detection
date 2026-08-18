export type TrainingStage = "stage1" | "stage2" | "stage3";

export type TrainingStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface LaunchTrainingRequest {
  stage: TrainingStage;
  dataset_path?: string | null;
  dataset_id?: string | null;
  config_path?: string | null;
  base_model?: string | null;
  device?: string;
  project_name?: string | null;
  run_name?: string | null;
  overrides?: Record<string, unknown>;
  recipe_id?: string | null;
  base_checkpoint_id?: string | null;
}

export interface TrainingJob {
  id: string;
  stage: TrainingStage;
  status: TrainingStatus;
  dataset_path: string;
  config_path: string | null;
  base_model: string | null;
  device: string;
  project_name: string;
  run_name: string;
  overrides: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  log_file: string | null;
  mlflow_run_id: string | null;
  error_message: string | null;
  job_type?: string;
  recipe_id?: string | null;
  base_checkpoint_id?: string | null;
  output_checkpoint_id?: string | null;
}

export interface JobListResponse {
  jobs: TrainingJob[];
  total: number;
}
