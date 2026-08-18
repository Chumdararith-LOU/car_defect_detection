export interface RunMetric {
  key: string;
  value: number;
}

export interface RunParam {
  key: string;
  value: string;
}

export interface ExperimentRun {
  run_id: string;
  run_name: string;
  experiment_name: string;
  status: string; // "RUNNING" | "FINISHED" | "FAILED" | "KILLED"
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  metrics: RunMetric[];
  params: RunParam[];
  artifact_uri: string | null;
}

export interface ExperimentSummary {
  experiment_id: string;
  name: string;
  run_count: number;
  latest_run_time: string | null;
}

export interface ExperimentListResponse {
  experiments: ExperimentSummary[];
}

export interface RunListResponse {
  runs: ExperimentRun[];
}

export interface RunComparisonResponse {
  runs: ExperimentRun[];
  best_run_id: string | null;
}
