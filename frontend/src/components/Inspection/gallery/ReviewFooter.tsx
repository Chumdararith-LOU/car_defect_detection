import { useState } from "react";
import type { OperatorDecision } from "@/lib/inspection/schema";
import { submitReview, updateReview } from "@/lib/inspection/apiClient";
import { DEFECT_CLASSES } from "@/lib/inspection/constants";
import { cn } from "@/lib/utils";

interface Props {
  inspectionId: string | null;
  predictedClass: string;
  predictedPanel: string;
  defectId?: string | null;
}

/** Shared operator feedback controls: confirm / reject / reclassify / unclear. */
export function ReviewFooter({
  inspectionId,
  predictedClass,
  predictedPanel,
  defectId,
}: Props) {
  const [decision, setDecision] = useState<OperatorDecision | null>(null);
  const [reclassifyClass, setReclassifyClass] = useState<string>(
    predictedClass !== "anomaly" ? predictedClass : "scratch",
  );
  const [submitting, setSubmitting] = useState(false);
  const [reviewed, setReviewed] = useState<OperatorDecision | null>(null);
  const [reviewId, setReviewId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canReview = Boolean(inspectionId) && !reviewed && !submitting;

  async function sendReview(
    operatorDecision: OperatorDecision,
    correctedClass: string | null = null,
  ) {
    if (!inspectionId) return;
    setSubmitting(true);
    setError(null);
    try {
      if (reviewId) {
        await updateReview(reviewId, {
          operator_decision: operatorDecision,
          corrected_class: correctedClass,
        });
      } else {
        const created = await submitReview({
          inspection_id: inspectionId,
          defect_id: defectId,
          predicted_class: predictedClass,
          predicted_panel: predictedPanel,
          operator_decision: operatorDecision,
          corrected_class: correctedClass,
        });
        setReviewId(created.id);
      }
      setReviewed(operatorDecision);
      setDecision(operatorDecision);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed");
    } finally {
      setSubmitting(false);
    }
  }

  const btn = (color: "green" | "red" | "blue" | "yellow", active = false) =>
    cn(
      "rounded-sm border px-2 py-1 font-mono text-[9px] uppercase tracking-wider transition disabled:cursor-not-allowed disabled:opacity-40",
      color === "green" &&
        "border-green-500/40 text-green-600 hover:bg-green-500/10 dark:text-green-400",
      color === "red" &&
        "border-red-500/40 text-red-600 hover:bg-red-500/10 dark:text-red-400",
      color === "blue" &&
        "border-blue-500/40 text-blue-600 hover:bg-blue-500/10 dark:text-blue-400",
      color === "yellow" &&
        "border-yellow-500/40 text-yellow-600 hover:bg-yellow-500/10 dark:text-yellow-400",
      active && "bg-blue-500/10",
    );

  if (reviewed) {
    return (
      <div className="flex items-center justify-between gap-2">
        <span
          className={cn(
            "rounded-sm px-2 py-1 font-mono text-[9px] uppercase tracking-wider",
            reviewed === "confirm" && "bg-green-500/15 text-green-600 dark:text-green-400",
            reviewed === "reject" && "bg-red-500/15 text-red-600 dark:text-red-400",
            reviewed === "reclassify" && "bg-blue-500/15 text-blue-600 dark:text-blue-400",
            reviewed === "unclear" && "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400",
          )}
        >
          Reviewed: {reviewed}
        </span>
        <button
          type="button"
          onClick={() => setReviewed(null)}
          className="rounded-sm border border-border px-2 py-0.5 font-mono text-[9px] uppercase text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
          title="Change your review decision"
        >
          Change
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        <button type="button" disabled={!canReview} onClick={() => void sendReview("confirm")} className={btn("green")}>
          Confirm
        </button>
        <button type="button" disabled={!canReview} onClick={() => void sendReview("reject")} className={btn("red")}>
          Reject
        </button>
        <button
          type="button"
          disabled={!canReview}
          onClick={() => setDecision(decision === "reclassify" ? null : "reclassify")}
          className={btn("blue", decision === "reclassify")}
        >
          Reclassify
        </button>
        <button type="button" disabled={!canReview} onClick={() => void sendReview("unclear")} className={btn("yellow")}>
          Unclear
        </button>
      </div>

      {decision === "reclassify" && (
        <div className="flex items-center gap-2">
          <select
            value={reclassifyClass}
            onChange={(e) => setReclassifyClass(e.target.value)}
            className="h-7 flex-1 rounded-sm border border-input bg-background px-2 font-mono text-[10px]"
          >
            {DEFECT_CLASSES.filter((c) => c.id !== "anomaly").map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={!canReview}
            onClick={() => void sendReview("reclassify", reclassifyClass)}
            className={btn("blue")}
          >
            Save
          </button>
        </div>
      )}
      {error && <p className="font-mono text-[9px] text-red-500">{error}</p>}
    </div>
  );
}
