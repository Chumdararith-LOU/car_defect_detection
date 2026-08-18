import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/Shared";
import {
  fetchReviewQueue,
  submitReview,
  updateReview,
  deleteReview,
} from "@/lib/inspection/apiClient";
import type {
  ReviewItem,
  ReviewCreate,
  ReviewUpdate,
  OperatorDecision,
} from "@/lib/inspection/schema";
import { createEmptyReviewForm } from "./reviewUtils";
import { ReviewSubmitForm } from "./ReviewSubmitForm";
import { ReviewHistoryList } from "./ReviewHistoryList";

export function ReviewDashboard() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<ReviewCreate>(createEmptyReviewForm());
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDecision, setEditDecision] = useState<OperatorDecision>("confirm");
  const [editCorrectedClass, setEditCorrectedClass] = useState<string>("scratch");
  const [updating, setUpdating] = useState(false);
  const [deleteReviewId, setDeleteReviewId] = useState<number | null>(null);

  const loadReviews = async () => {
    try {
      setLoading(true);
      const data = await fetchReviewQueue();
      setReviews(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
  }, []);

  const handleEdit = (review: ReviewItem) => {
    setEditingId(review.id);
    setEditDecision(review.operator_decision);
    setEditCorrectedClass(review.corrected_class || "scratch");
  };

  const handleDelete = (reviewId: number) => setDeleteReviewId(reviewId);

  const confirmDeleteReview = async () => {
    if (deleteReviewId === null) return;
    const reviewId = deleteReviewId;
    setDeleteReviewId(null);
    try {
      await deleteReview(reviewId);
      if (editingId === reviewId) setEditingId(null);
      toast.success("Review deleted");
      await loadReviews();
    } catch (e) {
      toast.error("Failed to delete review: " + (e instanceof Error ? e.message : String(e)));
    }
  };

  const handleUpdate = async (reviewId: number) => {
    setUpdating(true);
    try {
      const payload: ReviewUpdate = {
        operator_decision: editDecision,
        corrected_class: editDecision === "reclassify" ? editCorrectedClass : null,
      };
      await updateReview(reviewId, payload);
      setEditingId(null);
      toast.success("Review updated");
      await loadReviews();
    } catch (e) {
      toast.error("Failed to update review: " + (e instanceof Error ? e.message : String(e)));
    } finally {
      setUpdating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await submitReview(formData);
      setFormData(createEmptyReviewForm());
      toast.success("Review submitted");
      await loadReviews();
    } catch (e) {
      toast.error("Failed to submit review: " + (e instanceof Error ? e.message : String(e)));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Review Queue & History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Operator feedback loop. Currently showing the latest 50 submitted reviews from the
          backend.
        </p>
      </div>
      <ReviewSubmitForm
        formData={formData}
        setFormData={setFormData}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
      <ReviewHistoryList
        reviews={reviews}
        loading={loading}
        error={error}
        editingId={editingId}
        editDecision={editDecision}
        editCorrectedClass={editCorrectedClass}
        setEditDecision={setEditDecision}
        setEditCorrectedClass={setEditCorrectedClass}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onSave={handleUpdate}
        onCancel={() => setEditingId(null)}
        updating={updating}
      />
      <ConfirmDialog
        open={deleteReviewId !== null}
        onOpenChange={(o) => {
          if (!o) setDeleteReviewId(null);
        }}
        title="Delete review?"
        description="The review will be permanently removed. This cannot be undone."
        confirmLabel="Delete Review"
        onConfirm={confirmDeleteReview}
      />
    </div>
  );
}
