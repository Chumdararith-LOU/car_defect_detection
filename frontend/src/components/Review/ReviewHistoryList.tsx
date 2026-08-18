import type { ReviewItem, OperatorDecision } from "@/lib/inspection/schema";
import { DECISION_TONE_MAP } from "./reviewUtils";
import { StatusBadge } from "@/components/Shared";
import { ReviewEditForm } from "./ReviewEditForm";

interface Props {
  reviews: ReviewItem[];
  loading: boolean;
  error: string | null;
  editingId: number | null;
  editDecision: OperatorDecision;
  editCorrectedClass: string;
  setEditDecision: (decision: OperatorDecision) => void;
  setEditCorrectedClass: (cls: string) => void;
  onEdit: (review: ReviewItem) => void;
  onDelete: (reviewId: number) => void;
  onSave: (reviewId: number) => void;
  onCancel: () => void;
  updating: boolean;
}

export function ReviewHistoryList({
  reviews,
  loading,
  error,
  editingId,
  editDecision,
  editCorrectedClass,
  setEditDecision,
  setEditCorrectedClass,
  onEdit,
  onDelete,
  onSave,
  onCancel,
  updating,
}: Props) {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-medium">Review History ({reviews.length})</h3>
      </div>
      {loading && <div className="p-8 text-center text-muted-foreground">Loading reviews...</div>}
      {error && <div className="p-8 text-center text-destructive">Error: {error}</div>}
      {!loading && !error && reviews.length === 0 && (
        <div className="p-8 text-center text-muted-foreground">
          No reviews submitted yet. Use the form above to test the POST endpoint.
        </div>
      )}
      <div className="divide-y divide-border">
        {reviews.map((review) => (
          <div key={review.id} className="p-4 space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-2 text-sm">
              <div>
                <span className="font-mono text-xs text-muted-foreground">ID:</span> {review.id}
              </div>
              <div>
                <span className="font-mono text-xs text-muted-foreground">Insp:</span>{" "}
                {review.inspection_id}
              </div>
              <div>
                <span className="font-mono text-xs text-muted-foreground">Pred:</span>{" "}
                {review.predicted_class} / {review.predicted_panel}
              </div>
              <div>
                <span className="font-mono text-xs text-muted-foreground">Decision:</span>{" "}
                <StatusBadge tone={DECISION_TONE_MAP[review.operator_decision]} size="md">
                  {review.operator_decision}
                </StatusBadge>
                {review.corrected_class && (
                  <span className="ml-2 text-xs">→ {review.corrected_class}</span>
                )}
              </div>
              <div className="flex items-center justify-end gap-2">
                <button
                  onClick={() => onEdit(review)}
                  className="rounded border border-border px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(review.id)}
                  className="rounded border border-red-500/40 px-2 py-0.5 text-xs text-red-500 hover:bg-red-500/10"
                >
                  Delete
                </button>
                <span className="text-xs text-muted-foreground">
                  {new Date(review.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            {editingId === review.id && (
              <ReviewEditForm
                review={review}
                editDecision={editDecision}
                editCorrectedClass={editCorrectedClass}
                setEditDecision={setEditDecision}
                setEditCorrectedClass={setEditCorrectedClass}
                onSave={() => onSave(review.id)}
                onCancel={onCancel}
                updating={updating}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
