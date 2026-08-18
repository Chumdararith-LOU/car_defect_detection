import type { OperatorDecision, ReviewCreate } from "@/lib/inspection/schema";
import type { BadgeTone } from "@/components/Shared";

export const DECISION_TONE_MAP: Record<OperatorDecision, BadgeTone> = {
  confirm: "green",
  reject: "red",
  reclassify: "blue",
  unclear: "yellow",
};

export function createEmptyReviewForm(): ReviewCreate {
  return {
    inspection_id: "test-inspection-001",
    predicted_class: "scratch",
    predicted_panel: "hood",
    operator_decision: "confirm",
    corrected_class: null,
    notes: "",
  };
}
