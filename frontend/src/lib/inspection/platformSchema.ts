export type PlatformStage = "stage1" | "stage2" | "stage3";

export interface Taxonomy {
  id: string;
  name: string;
  stage: PlatformStage;
  class_names: string[];
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaxonomyListResponse {
  taxonomies: Taxonomy[];
  total: number;
}

export interface TaxonomyCreateRequest {
  name: string;
  stage: PlatformStage;
  class_names: string[];
  description?: string | null;
}

export interface TaxonomyUpdateRequest {
  name?: string;
  class_names?: string[];
  description?: string | null;
}

export type CheckpointOrigin = "native_coco" | "trained" | "surgery";

export interface Checkpoint {
  id: string;
  name: string;
  path: string;
  origin: CheckpointOrigin;
  source_checkpoint_id: string | null;
  source_job_id: string | null;
  stage: string;
  nc: number;
  class_names: string[] | null;
  architecture: string | null;
  created_at: string;
  notes: string | null;
  exists: boolean;
  size_mb: number | null;
}

export interface CheckpointListResponse {
  checkpoints: Checkpoint[];
  total: number;
}

export interface CheckpointScanResponse {
  registered: number;
  skipped: number;
}

export interface CheckpointRegisterRequest {
  name: string;
  path: string;
  origin?: CheckpointOrigin;
  stage?: string;
  nc?: number;
  class_names?: string[] | null;
  architecture?: string | null;
  source_checkpoint_id?: string | null;
  notes?: string | null;
}

export type HeadInitMode = "fresh" | "class_aware";

export interface SurgeryRequest {
  source_checkpoint_id: string;
  taxonomy_id: string;
  head_init_mode?: HeadInitMode;
}

export interface SurgeryStartResponse {
  job_id: string;
  status: string;
}

export interface SurgeryStatusResponse {
  job_id: string;
  status: string;
  error_message: string | null;
  output_checkpoint_id: string | null;
}

export type BaseStrategy = "native_coco" | "from_checkpoint" | "from_previous_step";
export type FreezeMode = "none" | "freeze_n" | "head_only";
export type LrMode = "uniform" | "differential";
export type LossType = "bce" | "focal" | "ce";

export interface Recipe {
  id: string;
  name: string;
  stage: PlatformStage;
  taxonomy_id: string;
  description: string | null;
  base_strategy: BaseStrategy;
  base_checkpoint_id: string | null;
  freeze_mode: FreezeMode;
  freeze_layers: number | null;
  lr_mode: LrMode;
  split_layer_idx: number | null;
  backbone_lr_mult: number | null;
  loss_type: LossType;
  fl_gamma: number;
  fl_alpha: number;
  fl_scale: number;
  imgsz: number;
  batch_size: number;
  epochs: number;
  optimizer: string;
  lr0: number;
  lrf: number;
  patience: number;
  augmentations: Record<string, unknown> | null;
  is_preset: boolean;
  created_at: string;
}

export interface RecipeListResponse {
  recipes: Recipe[];
  total: number;
}

export interface RecipeCreateRequest {
  name: string;
  taxonomy_id: string;
  description?: string | null;
  base_strategy?: BaseStrategy;
  base_checkpoint_id?: string | null;
  freeze_mode?: FreezeMode;
  freeze_layers?: number | null;
  lr_mode?: LrMode;
  split_layer_idx?: number | null;
  backbone_lr_mult?: number | null;
  loss_type?: LossType;
  fl_gamma?: number;
  fl_alpha?: number;
  fl_scale?: number;
  imgsz?: number;
  batch_size?: number;
  epochs?: number;
  optimizer?: string;
  lr0?: number;
  lrf?: number;
  patience?: number;
  augmentations?: Record<string, unknown> | null;
}

export type RecipeUpdateRequest = Partial<RecipeCreateRequest>;

export interface ChainStep {
  id: string;
  chain_id: string;
  order_index: number;
  recipe_id: string;
  dataset_id: string;
  base_source: string;
  base_checkpoint_id: string | null;
}

export interface Chain {
  id: string;
  name: string;
  stage: string;
  description: string | null;
  created_at: string;
  steps: ChainStep[];
}

export interface ChainListResponse {
  chains: Chain[];
  total: number;
}

export interface ChainRunStartResponse {
  run_id: string;
  status: string;
}

export interface ChainRunJobStatus {
  step_index: number;
  job_id: string;
  status: string;
}

export interface ChainRunStatusResponse {
  run_id: string;
  chain_id: string;
  status: string;
  current_step: number;
  jobs: ChainRunJobStatus[];
  error: string | null;
}

export interface AuditClassCount {
  class_id: number;
  name: string;
  instances: number;
  share: number;
}

export interface AuditSizeBuckets {
  p10_area: number;
  p60_area: number;
  bottom_10_count: number;
  middle_50_count: number;
  top_40_count: number;
}

export interface AuditLabelIssues {
  missing_label_images: number;
  empty_label_images: number;
  unparseable_lines: number;
  out_of_range_class_ids: number;
}

export interface AuditReport {
  dataset_id: string;
  stage: string;
  computed_at: string;
  totals: { images: number; instances: number };
  class_distribution: AuditClassCount[];
  rare_classes: string[];
  size_buckets: AuditSizeBuckets;
  label_issues: AuditLabelIssues;
  leakage: unknown;
  cleared_for_training: boolean;
  blocking_reasons: string[];
  warnings: string[];
}
