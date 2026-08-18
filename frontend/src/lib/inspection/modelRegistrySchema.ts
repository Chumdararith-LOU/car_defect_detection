export type ModelStatus = "candidate" | "champion" | "deployed" | "archived" | "rejected";
export type ModelStage = "stage1" | "stage2" | "stage3";

export interface GateResult {
  gate_name: string;
  passed: boolean;
  candidate_value: number | null;
  champion_value: number | null;
  threshold: string | null;
  reason: string | null;
}

export interface ModelVersion {
  id: string;
  stage: ModelStage;
  model_name: string;
  version: string;
  status: ModelStatus;
  weights_path: string;
  config_hash: string | null;
  dataset_version: string | null;
  training_run_id: string | null;
  metrics: Record<string, unknown>;
  evaluation_report: Record<string, unknown>;
  model_card: string | null;
  created_at: string;
  promoted_at: string | null;
  deployed_at: string | null;
}

export interface ModelRegistryListResponse {
  models: ModelVersion[];
  total: number;
}

export interface RegisterModelRequest {
  stage: ModelStage;
  model_name: string;
  version: string;
  weights_path: string;
  config_hash?: string | null;
  dataset_version?: string | null;
  training_run_id?: string | null;
  metrics?: Record<string, unknown>;
  model_card?: string | null;
}

export interface PromotionResponse {
  model_id: string;
  promoted: boolean;
  gate_results: GateResult[];
  message: string;
}

export interface DeploymentResponse {
  model_id: string;
  deployed: boolean;
  message: string;
}

export interface RollbackResponse {
  stage: ModelStage;
  rolled_back: boolean;
  previous_model_id: string | null;
  current_model_id: string | null;
  message: string;
}

export interface GatePreviewResponse {
  model_id: string;
  gate_results: GateResult[];
  all_passed: boolean;
}
