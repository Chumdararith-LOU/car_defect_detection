export type DefectClass =
  | "anomaly"
  | "dent"
  | "scratch"
  | "crack"
  | "glass_shatter"
  | "broken_lamp"
  | "corrosion"
  | "disjoint_part";
export type PanelId =
  | "quarter_panel"
  | "front_wheel"
  | "back_window"
  | "trunk"
  | "front_door"
  | "rocker_panel"
  | "grille"
  | "windshield"
  | "front_window"
  | "back_door"
  | "headlight"
  | "back_wheel"
  | "back_windshield"
  | "hood"
  | "fender"
  | "tail_light"
  | "license_plate"
  | "front_bumper"
  | "back_bumper"
  | "mirror"
  | "roof"
  | "Unknown";
export type PipelineStage =
  | "idle"
  | "prescreen"
  | "tiling"
  | "context"
  | "processing"
  | "done"
  | "error";
export type OperatorDecision = "confirm" | "reject" | "reclassify" | "unclear";

export type ViewStage = 1 | 2 | 3;

export interface ImageDims {
  width: number;
  height: number;
}

export interface PreScreenResult {
  anomalyDetected: boolean;
  score: number;
  latencyMs: number;
}

export interface Panel {
  id: string;
  label: string;
  polygon: [number, number][];
  activeArea?: number;
}

export interface Defect {
  id: string;
  class: DefectClass;
  confidence: number;
  bbox: [number, number, number, number];
  polygon: [number, number][];
  panel: PanelId;
  iod: number;
  dsi: number | null;
}

export interface UnclassifiedAnomaly {
  id: string;
  confidence: number;
  bbox: [number, number, number, number];
  polygon?: [number, number][];
  panel: PanelId;
  reason: string;
  low_context?: boolean;
}

export interface SuppressedDetection {
  id: string;
  predicted_class: DefectClass;
  confidence: number;
  bbox: [number, number, number, number];
  polygon?: [number, number][];
  panel: PanelId;
  reason: string;
}

export interface Stage1Blob {
  id: string;
  bbox: [number, number, number, number];
  polygon: [number, number][];
  area_ratio: number;
}

export interface InspectionPayload {
  inspection_id: string;
  timestamp: string;
  vehicle_color_detected: string;
  total_defects_found: number;
  inspection_status: "PASS" | "FAIL";
  imageDims?: ImageDims;
  preScreen?: PreScreenResult | null;
  panels?: Panel[];
  defects: Defect[];
  unclassified_anomalies?: UnclassifiedAnomaly[];
  suppressed_detections?: SuppressedDetection[];
  stage1_blobs?: Stage1Blob[];
  disabled_stages?: string[];
}

export interface ReviewItem {
  id: number;
  inspection_id: string;
  defect_id: string | null;
  model_version: string | null;
  predicted_class: string | null;
  predicted_panel: string | null;
  operator_decision: OperatorDecision;
  corrected_class: string | null;
  notes: string | null;
  created_at: string;
}

export interface ReviewCreate {
  inspection_id: string;
  defect_id?: string | null;
  model_version?: string | null;
  predicted_class?: string | null;
  predicted_panel?: string | null;
  operator_decision: OperatorDecision;
  corrected_class?: string | null;
  notes?: string | null;
}

export interface ReviewUpdate {
  operator_decision?: OperatorDecision;
  corrected_class?: string | null;
  notes?: string | null;
}

export type DatasetStage = "stage1" | "stage2" | "stage3";
export type DatasetStatus = "raw" | "curated" | "released" | "archived";

export interface SplitInfo {
  name: string;
  image_count: number;
  path: string;
}

export interface ClassDistributionItem {
  class_id: number;
  class_name: string;
  instance_count: number;
  percentage: number;
}

export interface DatasetSummary {
  dataset_id: string;
  name: string;
  stage: DatasetStage;
  yaml_path: string;
  nc: number;
  class_names: string[];
  splits: SplitInfo[];
  total_images: number;
  is_champion: boolean;
  status: DatasetStatus;
}

export interface DatasetDetail extends DatasetSummary {
  root_path: string;
  class_distribution: ClassDistributionItem[];
}

export interface FilenameOverlap {
  filename: string;
  found_in: string[];
}

export interface LeakageAuditResult {
  dataset_id: string;
  passed: boolean;
  total_checked: number;
  filename_overlaps: FilenameOverlap[];
  issues: string[];
}

export interface DatasetBuildRequest {
  stage: DatasetStage;
  version_name: string;
  include_confirmed: boolean;
  include_rejected: boolean;
  include_unclear: boolean;
  notes?: string | null;
}

export interface DatasetBuildResponse {
  dataset_id: string;
  version_name: string;
  status: DatasetStatus;
  message: string;
}

export interface DatasetImageAnnotation {
  index: number;
  class_id: number;
  class_name: string;
  polygon: [number, number][];
}

export interface DatasetImageLabelsResponse {
  filename: string;
  dataset_id: string;
  split: string;
  annotation_count: number;
  annotations: DatasetImageAnnotation[];
  class_names: string[];
}

export interface ReclassifyResponse {
  success: boolean;
  message: string;
  old_class_id: number;
  new_class_id: number;
}

export interface DatasetImageListResponse {
  images: string[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SavedInspection {
  inspection_id: string;
  image_filename: string | null;
  defect_count: number;
  inspection_status: string;
  timestamp: string;
}

export interface InspectionListResponse {
  inspections: SavedInspection[];
  total: number;
}

export interface ImportResponse {
  success: boolean;
  message: string;
  image_filename: string;
  labels_written: number;
  stats?: { images: number; labels: number; skipped: number };
}
