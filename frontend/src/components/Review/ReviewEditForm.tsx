import type { ReviewItem, OperatorDecision } from "@/lib/inspection/schema";
import { DEFECT_CLASSES } from "@/lib/inspection/constants";

interface Props {
  review: ReviewItem;
  editDecision: OperatorDecision;
  editCorrectedClass: string;
  setEditDecision: (decision: OperatorDecision) => void;
  setEditCorrectedClass: (cls: string) => void;
  onSave: () => void;
  onCancel: () => void;
  updating: boolean;
}

export function ReviewEditForm({
  editDecision,
  editCorrectedClass,
  setEditDecision,
  setEditCorrectedClass,
  onSave,
  onCancel,
  updating,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded border border-border bg-background p-3">
      <label className="text-xs font-medium">Decision:</label>
      <select
        value={editDecision}
        onChange={(e) => setEditDecision(e.target.value as OperatorDecision)}
        className="rounded border border-input bg-background px-2 py-1 text-xs"
      >
        <option value="confirm">Confirm</option>
        <option value="reject">Reject</option>
        <option value="reclassify">Reclassify</option>
        <option value="unclear">Unclear</option>
      </select>
      {editDecision === "reclassify" && (
        <>
          <label className="text-xs font-medium">Corrected:</label>
          <select
            value={editCorrectedClass}
            onChange={(e) => setEditCorrectedClass(e.target.value)}
            className="rounded border border-input bg-background px-2 py-1 text-xs"
          >
            {DEFECT_CLASSES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </>
      )}
      <button
        onClick={onSave}
        disabled={updating}
        className="rounded bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {updating ? "Saving..." : "Save"}
      </button>
      <button
        onClick={onCancel}
        className="rounded border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-accent"
      >
        Cancel
      </button>
    </div>
  );
}
