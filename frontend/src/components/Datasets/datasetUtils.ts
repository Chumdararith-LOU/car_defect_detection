import type { DatasetStage, DatasetStatus } from "@/lib/inspection/schema";
import type { BadgeTone } from "@/components/Shared";

export function getStageBadgeTone(stage: DatasetStage): BadgeTone {
  switch (stage) {
    case "stage1":
      return "blue";
    case "stage2":
      return "purple";
    case "stage3":
      return "emerald";
    default:
      return "gray";
  }
}

export function getStatusBadgeTone(status: DatasetStatus): BadgeTone {
  switch (status) {
    case "released":
      return "green";
    case "curated":
      return "yellow";
    case "raw":
      return "gray";
    case "archived":
      return "red";
    default:
      return "gray";
  }
}
