/**
 * Types for the Dataset Preparation module:
 * whole-dataset import, split-structure detection, re-split, and tiling.
 * Mirrors backend/schemas/dataset_prep.py
 */

export type SplitLayout =
  | "ultralytics"
  | "grouped"
  | "unsplit"
  | "flat"
  | "unknown";

export interface DetectedSplit {
  name: string; // "train" | "val" | "test" | "all"
  image_count: number;
  label_count: number;
  images_path: string;
  labels_path: string | null;
  label_format: string | null; // "yolo_txt" | "semantic_mask" | null
}

export interface SplitStructure {
  dataset_id: string;
  layout: SplitLayout;
  has_data_yaml: boolean;
  splits: DetectedSplit[];
  total_images: number;
  total_labels: number;
  is_split: boolean;
  has_test: boolean;
  warnings: string[];
}

export interface ImportDatasetResponse {
  success: boolean;
  dataset_id: string;
  path: string;
  structure: SplitStructure;
  message: string;
}

export interface ResplitRequest {
  train_ratio: number;
  val_ratio: number;
  test_ratio: number;
  seed: number;
}

export interface ResplitResponse {
  success: boolean;
  dataset_id: string;
  new_structure: SplitStructure;
  message: string;
}

export interface TileRequest {
  new_dataset_id: string;
  tile_size: number; // 0 = legacy adaptive 2x2 halving
  overlap: number;
  min_area_ratio: number;
}

export interface TileResponse {
  success: boolean;
  original_dataset_id: string;
  new_dataset_id: string;
  tiles_generated: number;
  message: string;
}
