import type { ModelStatus, ModelStage } from "@/lib/inspection/modelRegistrySchema";
import type { BadgeTone } from "@/components/Shared";

export const STATUS_TONE_MAP: Record<ModelStatus, BadgeTone> = {
  candidate: "yellow",
  champion: "green",
  deployed: "blue",
  archived: "gray",
  rejected: "red",
};

export const STAGE_LABEL_MAP: Record<ModelStage, string> = {
  stage1: "Stage 1 (SOD)",
  stage2: "Stage 2 (Defect)",
  stage3: "Stage 3 (Panel)",
};

export function formatMetricValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toFixed(4);
  return String(value);
}

export function formatDate(isoString: string | null): string {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleString();
}

export function getPrimaryMetric(
  metrics: Record<string, unknown>,
  stage: ModelStage,
): { key: string; value: string } {
  if (stage === "stage1") {
    const recall = metrics["recall"];
    return { key: "Recall", value: formatMetricValue(recall) };
  }
  const map50 = metrics["test_mask_map50"];
  return { key: "mAP50", value: formatMetricValue(map50) };
}

export function shortDatasetName(path: string | null): string {
  if (!path) return "—";
  const segments = path.split("/").filter(Boolean);
  if (segments.length === 0) return "—";
  const last = segments[segments.length - 1];
  if (last.endsWith(".yaml") || last.endsWith(".yml")) {
    return segments.length > 1 ? segments[segments.length - 2] : last;
  }
  return last;
}
