import type {
  InspectionPayload,
  ReviewItem,
  ReviewCreate,
  ReviewUpdate,
  DatasetSummary,
  DatasetDetail,
  LeakageAuditResult,
  DatasetBuildRequest,
  DatasetBuildResponse,
  DatasetImageListResponse,
  DatasetImageLabelsResponse,
  ReclassifyResponse,
  InspectionListResponse,
  ImportResponse,
  DatasetStage,
} from "./schema";
import type {
  ImportDatasetResponse,
  ResplitRequest,
  ResplitResponse,
  SplitStructure,
  TileRequest,
  TileResponse,
} from "./prepSchema";
import type { LaunchTrainingRequest, TrainingJob, JobListResponse } from "./trainingSchema";
import type {
  ExperimentListResponse,
  RunListResponse,
  RunComparisonResponse,
} from "./experimentSchema";
import type {
  ModelRegistryListResponse,
  ModelVersion,
  PromotionResponse,
  DeploymentResponse,
  RollbackResponse,
  GatePreviewResponse,
  ModelStage,
  ModelStatus,
} from "./modelRegistrySchema";
import type {
  AuditReport,
  Checkpoint,
  CheckpointListResponse,
  CheckpointRegisterRequest,
  CheckpointScanResponse,
  Chain,
  ChainListResponse,
  ChainRunStartResponse,
  ChainRunStatusResponse,
  Recipe,
  RecipeCreateRequest,
  RecipeListResponse,
  RecipeUpdateRequest,
  SurgeryRequest,
  SurgeryStartResponse,
  SurgeryStatusResponse,
  Taxonomy,
  TaxonomyCreateRequest,
  TaxonomyListResponse,
  TaxonomyUpdateRequest,
} from "./platformSchema";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export interface ModelListResponse {
  models: string[];
  stage1: string[];
  stage2: string[];
  stage3: string[];
}

export type Stage2Mode = "direct" | "sahi";
export type Stage2Preset = "balanced" | "safety" | "max_recall";

export interface InspectParams {
  file: File;
  modelName?: string;
  stage2ModelName?: string;
  stage2Mode?: Stage2Mode;
  stage2Preset?: Stage2Preset;
  stage2Conf?: number;
  device?: string;
  enableStage1?: boolean;
  enableStage2?: boolean;
  enableStage3?: boolean;
}

export async function fetchModels(): Promise<ModelListResponse> {
  const res = await fetch(`${API_BASE}/api/models`);
  if (!res.ok) throw new Error(`Failed to fetch models: ${res.statusText}`);
  return res.json();
}

export async function runInspection(params: InspectParams): Promise<InspectionPayload> {
  const formData = new FormData();
  formData.append("file", params.file);

  if (params.modelName) {
    formData.append("model_name", params.modelName);
  }
  if (params.stage2ModelName) {
    formData.append("stage2_model_name", params.stage2ModelName);
  }
  if (params.stage2Mode) {
    formData.append("stage2_mode", params.stage2Mode);
  }
  if (params.stage2Preset) {
    formData.append("stage2_preset", params.stage2Preset);
  }
  if (params.stage2Conf !== undefined) {
    formData.append("stage2_conf", String(params.stage2Conf));
  }
  if (params.device) {
    formData.append("device", params.device);
  }
  formData.append("enable_stage1", String(params.enableStage1 ?? true));
  formData.append("enable_stage2", String(params.enableStage2 ?? true));
  formData.append("enable_stage3", String(params.enableStage3 ?? true));

  const res = await fetch(`${API_BASE}/api/inspect`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
  return res.json();
}

export interface SystemDevices {
  cpu: boolean;
  cuda: boolean;
  mps: boolean;
  cuda_name: string | null;
  platform: string;
}

/** Flat metrics shape returned by GET /api/system/metrics (backend/api/system.py). */
export interface SystemMetrics {
  cpu_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  /** Whatever GPU name the backend detected (e.g. "Apple Silicon (MPS)", "NVIDIA ..."), or null if no GPU. */
  gpu_name: string | null;
  gpu_utilization_percent: number | null;
  gpu_vram_used_gb: number | null;
  gpu_vram_total_gb: number | null;
}

export async function fetchSystemDevices(): Promise<SystemDevices> {
  const res = await fetch(`${API_BASE}/api/system/devices`);
  if (!res.ok) throw new Error("Failed to fetch devices");
  return res.json();
}

export async function fetchSystemMetrics(): Promise<SystemMetrics> {
  const res = await fetch(`${API_BASE}/api/system/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export interface HostProfile {
  schema_version: string;
  machine: {
    hostname: string;
    os: string;
    platform: string;
    architecture: string;
    python_version: string;
  };
  cpu: {
    logical_cores: number;
    physical_cores: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
  };
  disk: {
    workspace_path: string;
    free_gb: number;
    total_gb: number;
  };
  gpu: {
    cuda_available: boolean;
    mps_available: boolean;
    device_count: number;
    devices: Array<{
      index: number;
      name: string;
      total_vram_gb: number | null;
      free_vram_gb: number | null;
    }>;
  };
  models: {
    stage1: { available: boolean; version: string | null; path_status: string };
    stage2: { available: boolean; version: string | null; path_status: string };
    stage3: { available: boolean; version: string | null; path_status: string };
    stage4: { available: boolean; config_status: string };
  };
  capabilities: {
    can_infer_stage1: boolean;
    can_infer_stage2: boolean;
    can_infer_stage3: boolean;
    can_use_local_gpu: boolean;
  };
  recommendations: {
    runtime_mode: string;
    inference_device: string;
    training_device: string;
  };
  warnings: string[];
}

export async function fetchHostProfile(): Promise<HostProfile> {
  const res = await fetch(`${API_BASE}/api/host/profile`);
  if (!res.ok) throw new Error(`Failed to fetch host profile: ${res.statusText}`);
  return res.json();
}

export async function fetchReviewQueue(): Promise<ReviewItem[]> {
  const res = await fetch(`${API_BASE}/api/review-queue`);
  if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.statusText}`);
  return res.json();
}

export async function submitReview(payload: ReviewCreate): Promise<ReviewItem> {
  const res = await fetch(`${API_BASE}/api/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to submit review: ${res.statusText}`);
  return res.json();
}

export async function updateReview(reviewId: number, payload: ReviewUpdate): Promise<ReviewItem> {
  const res = await fetch(`${API_BASE}/api/reviews/${reviewId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to update review: ${res.statusText}`);
  return res.json();
}

export async function deleteReview(reviewId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/reviews/${reviewId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete review: ${res.statusText}`);
}

export interface DatasetListResponse {
  datasets: DatasetSummary[];
}

export async function fetchDatasets(): Promise<DatasetListResponse> {
  const res = await fetch(`${API_BASE}/api/datasets`);
  if (!res.ok) throw new Error(`Failed to fetch datasets: ${res.statusText}`);
  return res.json();
}

export async function fetchDatasetDetail(datasetId: string): Promise<DatasetDetail> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}`);
  if (!res.ok) throw new Error(`Failed to fetch dataset detail: ${res.statusText}`);
  return res.json();
}

export async function runLeakageAudit(datasetId: string): Promise<LeakageAuditResult> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/audit`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to run leakage audit: ${res.statusText}`);
  return res.json();
}

export async function fetchAllReviews(): Promise<ReviewItem[]> {
  const res = await fetch(`${API_BASE}/api/reviews`);
  if (!res.ok) throw new Error(`Failed to fetch reviews: ${res.statusText}`);
  return res.json();
}

export async function buildDataset(request: DatasetBuildRequest): Promise<DatasetBuildResponse> {
  const res = await fetch(`${API_BASE}/api/datasets/build`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`Failed to build dataset: ${res.statusText}`);
  return res.json();
}

export function getDatasetImageUrl(datasetId: string, filename: string, split = "train"): string {
  return `${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}?split=${split}`;
}

export async function fetchDatasetImages(
  datasetId: string,
  page = 1,
  size = 20,
  split = "train",
): Promise<DatasetImageListResponse> {
  const res = await fetch(
    `${API_BASE}/api/datasets/${datasetId}/images?page=${page}&size=${size}&split=${split}`,
  );
  if (!res.ok) throw new Error(`Failed to fetch dataset images: ${res.statusText}`);
  return res.json();
}

export async function fetchDatasetImageLabels(
  datasetId: string,
  filename: string,
  split = "train",
): Promise<DatasetImageLabelsResponse> {
  const res = await fetch(
    `${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}/labels?split=${split}`,
  );
  if (!res.ok) throw new Error(`Failed to fetch image labels: ${res.statusText}`);
  return res.json();
}

export async function reclassifyAnnotation(
  datasetId: string,
  filename: string,
  annotationIndex: number,
  newClassId: number,
  split = "train",
): Promise<ReclassifyResponse> {
  const res = await fetch(
    `${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}/labels/${annotationIndex}?split=${split}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_class_id: newClassId }),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Reclassify failed: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteAnnotation(
  datasetId: string,
  filename: string,
  annotationIndex: number,
  split = "train",
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(
    `${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}/labels/${annotationIndex}?split=${split}`,
    {
      method: "DELETE",
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Delete failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAvailableInspections(limit = 50): Promise<InspectionListResponse> {
  const res = await fetch(`${API_BASE}/api/import/inspections?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch inspections: ${res.statusText}`);
  return res.json();
}

export async function deleteInspection(inspectionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/import/inspections/${inspectionId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to delete inspection");
  }
}

export async function importInspectionToDataset(
  datasetId: string,
  inspectionId: string,
  split = "train",
): Promise<ImportResponse> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/import/inspection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inspection_id: inspectionId, split }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Import failed: ${res.statusText}`);
  }
  return res.json();
}

export async function uploadImageToDataset(
  datasetId: string,
  file: File,
  split = "train",
): Promise<ImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("split", split);

  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/import/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Upload failed: ${res.statusText}`);
  }
  return res.json();
}

export async function createNewDataset(
  versionName: string,
  stage: DatasetStage,
  notes: string | null = null,
): Promise<unknown> {
  const res = await fetch(`${API_BASE}/api/datasets/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ version_name: versionName, stage, notes }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Create dataset failed: ${res.statusText}`);
  }
  return res.json();
}

export async function importZipToDataset(
  datasetId: string,
  file: File,
  split = "train",
): Promise<ImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("split", split);

  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/import/zip`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `ZIP import failed: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteDataset(datasetId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to delete dataset: ${res.statusText}`);
  }
}

export async function importDatasetZip(
  file: File,
  versionName: string,
): Promise<ImportDatasetResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("version_name", versionName);
  const res = await fetch(`${API_BASE}/api/datasets/import-dataset`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Import dataset failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSplitStructure(datasetId: string): Promise<SplitStructure> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/split-structure`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Split detection failed: ${res.statusText}`);
  }
  return res.json();
}

export async function resplitDataset(
  datasetId: string,
  request: ResplitRequest,
): Promise<ResplitResponse> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/resplit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Resplit failed: ${res.statusText}`);
  }
  return res.json();
}

export async function tileDataset(datasetId: string, request: TileRequest): Promise<TileResponse> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/tile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Tiling failed: ${res.statusText}`);
  }
  return res.json();
}

export async function launchTrainingJob(request: LaunchTrainingRequest): Promise<TrainingJob> {
  const res = await fetch(`${API_BASE}/api/training/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to launch training job: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTrainingJobs(limit = 50, offset = 0): Promise<JobListResponse> {
  const res = await fetch(`${API_BASE}/api/training/jobs?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error(`Failed to fetch training jobs: ${res.statusText}`);
  return res.json();
}

export async function fetchTrainingJobDetail(jobId: string): Promise<TrainingJob> {
  const res = await fetch(`${API_BASE}/api/training/jobs/${jobId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to fetch job detail: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTrainingJobLogs(jobId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/training/jobs/${jobId}/logs`);
  if (!res.ok) throw new Error(`Failed to fetch logs: ${res.statusText}`);
  return res.text();
}

export async function stopTrainingJob(
  jobId: string,
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/training/jobs/${jobId}/stop`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to stop job: ${res.statusText}`);
  }
  return res.json();
}

export interface TrainingConfigTemplate {
  project_name?: string;
  run_name?: string;
  model_preset?: string;
  device?: string | number;
  epochs?: number;
  imgsz?: number;
  batch_size?: number;
  [key: string]: string | number | boolean | null | undefined;
}

export async function fetchConfigTemplate(stage: string): Promise<{
  stage: string;
  template: TrainingConfigTemplate;
  source_path: string;
}> {
  const res = await fetch(`${API_BASE}/api/training/config-template?stage=${stage}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to fetch template: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchExperiments(): Promise<ExperimentListResponse> {
  const res = await fetch(`${API_BASE}/api/experiments`);
  if (!res.ok) throw new Error(`Failed to fetch experiments: ${res.statusText}`);
  return res.json();
}

export async function fetchExperimentRuns(experimentId: string): Promise<RunListResponse> {
  const res = await fetch(`${API_BASE}/api/experiments/${experimentId}/runs`);
  if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`);
  return res.json();
}

export async function compareRuns(runIds: string[]): Promise<RunComparisonResponse> {
  const res = await fetch(`${API_BASE}/api/experiments/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_ids: runIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to compare runs: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchModelRegistryModels(
  stage?: ModelStage,
  status?: ModelStatus,
): Promise<ModelRegistryListResponse> {
  let url = `${API_BASE}/api/model-registry`;
  const params = new URLSearchParams();
  if (stage) params.set("stage", stage);
  if (status) params.set("status", status);
  if (params.toString()) url += `?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch model registry: ${res.statusText}`);
  return res.json();
}

export async function fetchModelDetail(modelId: string): Promise<ModelVersion> {
  const res = await fetch(`${API_BASE}/api/model-registry/${modelId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to fetch model detail: ${res.statusText}`);
  }
  return res.json();
}

export async function evaluateModelGates(modelId: string): Promise<GatePreviewResponse> {
  const res = await fetch(`${API_BASE}/api/model-registry/${modelId}/evaluate`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to evaluate gates: ${res.statusText}`);
  }
  return res.json();
}

export async function promoteModel(modelId: string): Promise<PromotionResponse> {
  const res = await fetch(`${API_BASE}/api/model-registry/${modelId}/promote`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to promote model: ${res.statusText}`);
  }
  return res.json();
}

export async function deployModel(modelId: string): Promise<DeploymentResponse> {
  const res = await fetch(`${API_BASE}/api/model-registry/${modelId}/deploy`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to deploy model: ${res.statusText}`);
  }
  return res.json();
}

export async function rollbackModel(stage: ModelStage): Promise<RollbackResponse> {
  const res = await fetch(`${API_BASE}/api/model-registry/stage/${stage}/rollback`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to rollback model: ${res.statusText}`);
  }
  return res.json();
}

export async function listTaxonomies(stage?: string): Promise<TaxonomyListResponse> {
  let url = `${API_BASE}/api/taxonomies`;
  const params = new URLSearchParams();
  if (stage) params.set("stage", stage);
  if (params.toString()) url += `?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to list taxonomies: ${res.statusText}`);
  }
  return res.json();
}

export async function createTaxonomy(req: TaxonomyCreateRequest): Promise<Taxonomy> {
  const res = await fetch(`${API_BASE}/api/taxonomies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to create taxonomy: ${res.statusText}`);
  }
  return res.json();
}

export async function updateTaxonomy(id: string, req: TaxonomyUpdateRequest): Promise<Taxonomy> {
  const res = await fetch(`${API_BASE}/api/taxonomies/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to update taxonomy: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteTaxonomy(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/taxonomies/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to delete taxonomy: ${res.statusText}`);
  }
}

export async function listCheckpoints(stage?: string): Promise<CheckpointListResponse> {
  let url = `${API_BASE}/api/checkpoints`;
  const params = new URLSearchParams();
  if (stage) params.set("stage", stage);
  if (params.toString()) url += `?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to list checkpoints: ${res.statusText}`);
  }
  return res.json();
}

export async function scanCheckpoints(): Promise<CheckpointScanResponse> {
  const res = await fetch(`${API_BASE}/api/checkpoints/scan`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to scan checkpoints: ${res.statusText}`);
  }
  return res.json();
}

export async function registerCheckpoint(req: CheckpointRegisterRequest): Promise<Checkpoint> {
  const res = await fetch(`${API_BASE}/api/checkpoints/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to register checkpoint: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteCheckpoint(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/checkpoints/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to delete checkpoint: ${res.statusText}`);
  }
}

export async function startSurgery(req: SurgeryRequest): Promise<SurgeryStartResponse> {
  const res = await fetch(`${API_BASE}/api/surgery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to start surgery: ${res.statusText}`);
  }
  return res.json();
}

export async function getSurgeryStatus(jobId: string): Promise<SurgeryStatusResponse> {
  const res = await fetch(`${API_BASE}/api/surgery/${jobId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to get surgery status: ${res.statusText}`);
  }
  return res.json();
}

export async function listRecipes(stage?: string): Promise<RecipeListResponse> {
  let url = `${API_BASE}/api/recipes`;
  const params = new URLSearchParams();
  if (stage) params.set("stage", stage);
  if (params.toString()) url += `?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to list recipes: ${res.statusText}`);
  }
  return res.json();
}

export async function listRecipePresets(): Promise<RecipeListResponse> {
  const res = await fetch(`${API_BASE}/api/recipes/presets`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to list presets: ${res.statusText}`);
  }
  return res.json();
}

export async function createRecipe(req: RecipeCreateRequest): Promise<Recipe> {
  const res = await fetch(`${API_BASE}/api/recipes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to create recipe: ${res.statusText}`);
  }
  return res.json();
}

export async function updateRecipe(id: string, req: RecipeUpdateRequest): Promise<Recipe> {
  const res = await fetch(`${API_BASE}/api/recipes/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to update recipe: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteRecipe(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/recipes/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to delete recipe: ${res.statusText}`);
  }
}

export async function listChains(): Promise<ChainListResponse> {
  const res = await fetch(`${API_BASE}/api/chains`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to list chains: ${res.statusText}`);
  }
  return res.json();
}

export async function startChainRun(chainId: string): Promise<ChainRunStartResponse> {
  const res = await fetch(`${API_BASE}/api/chains/${chainId}/run`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to start chain run: ${res.statusText}`);
  }
  return res.json();
}

export async function getChainRunStatus(runId: string): Promise<ChainRunStatusResponse> {
  const res = await fetch(`${API_BASE}/api/chains/runs/${runId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to get chain run status: ${res.statusText}`);
  }
  return res.json();
}

export async function runFullDatasetAudit(datasetId: string): Promise<AuditReport> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/audit/full`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to run full audit: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDatasetAuditReport(datasetId: string): Promise<AuditReport | null> {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/audit/report`);
  if (res.status === 404) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to fetch audit report: ${res.statusText}`);
  }
  return res.json();
}
