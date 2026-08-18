import type { ReviewCreate, OperatorDecision } from "@/lib/inspection/schema";
import {
  DEFECT_CLASSES,
  PANEL_LABELS,
  ALL_PANELS,
} from "@/lib/inspection/constants";

interface Props {
  formData: ReviewCreate;
  setFormData: React.Dispatch<React.SetStateAction<ReviewCreate>>;
  onSubmit: (e: React.FormEvent) => void;
  submitting: boolean;
}

export function ReviewSubmitForm({
  formData,
  setFormData,
  onSubmit,
  submitting,
}: Props) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
      <h3 className="text-lg font-medium">Submit Test Review</h3>
      <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Inspection ID</label>
          <input
            type="text"
            required
            value={formData.inspection_id}
            onChange={(e) =>
              setFormData({ ...formData, inspection_id: e.target.value })
            }
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Predicted Class</label>
          <select
            value={formData.predicted_class || ""}
            onChange={(e) =>
              setFormData({ ...formData, predicted_class: e.target.value })
            }
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {DEFECT_CLASSES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Predicted Panel</label>
          <select
            value={formData.predicted_panel || ""}
            onChange={(e) =>
              setFormData({ ...formData, predicted_panel: e.target.value })
            }
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {ALL_PANELS.map((p) => (
              <option key={p} value={p}>
                {PANEL_LABELS[p]}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Decision</label>
          <select
            value={formData.operator_decision}
            onChange={(e) => {
              const decision = e.target.value as OperatorDecision;
              setFormData({
                ...formData,
                operator_decision: decision,
                corrected_class:
                  decision === "reclassify"
                    ? formData.corrected_class || "dent"
                    : null,
              });
            }}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="confirm">Confirm</option>
            <option value="reject">Reject (False Positive)</option>
            <option value="reclassify">Reclassify</option>
            <option value="unclear">Unclear</option>
          </select>
        </div>
        {formData.operator_decision === "reclassify" && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Corrected Class</label>
            <select
              value={formData.corrected_class || ""}
              onChange={(e) =>
                setFormData({ ...formData, corrected_class: e.target.value })
              }
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {DEFECT_CLASSES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-medium">Notes</label>
          <textarea
            value={formData.notes || ""}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px]"
            placeholder="Optional notes..."
          />
        </div>
        <div className="md:col-span-2 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Review"}
          </button>
        </div>
      </form>
    </div>
  );
}
