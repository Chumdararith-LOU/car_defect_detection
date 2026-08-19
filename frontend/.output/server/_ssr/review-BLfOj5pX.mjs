import { n as __toESM } from "../_runtime.mjs";
import { T as fetchReviewQueue, it as updateReview, l as deleteReview, nt as submitReview } from "./apiClient-ClfACpV5.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { l as StatusBadge } from "./alert-dialog-DsQ-Uqlb.mjs";
import { t as ConfirmDialog } from "./ConfirmDialog-CbIeVXtH.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { n as DEFECT_CLASSES, r as PANEL_LABELS, t as ALL_PANELS } from "./constants-CrQ5z6ae.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/review-BLfOj5pX.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var DECISION_TONE_MAP = {
	confirm: "green",
	reject: "red",
	reclassify: "blue",
	unclear: "yellow"
};
function createEmptyReviewForm() {
	return {
		inspection_id: "test-inspection-001",
		predicted_class: "scratch",
		predicted_panel: "hood",
		operator_decision: "confirm",
		corrected_class: null,
		notes: ""
	};
}
function ReviewSubmitForm({ formData, setFormData, onSubmit, submitting }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-lg border border-border bg-card p-6 space-y-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
			className: "text-lg font-medium",
			children: "Submit Test Review"
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
			onSubmit,
			className: "grid grid-cols-1 md:grid-cols-2 gap-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Inspection ID"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
						type: "text",
						required: true,
						value: formData.inspection_id,
						onChange: (e) => setFormData({
							...formData,
							inspection_id: e.target.value
						}),
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Predicted Class"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
						value: formData.predicted_class || "",
						onChange: (e) => setFormData({
							...formData,
							predicted_class: e.target.value
						}),
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
						children: DEFECT_CLASSES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
							value: c.id,
							children: c.label
						}, c.id))
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Predicted Panel"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
						value: formData.predicted_panel || "",
						onChange: (e) => setFormData({
							...formData,
							predicted_panel: e.target.value
						}),
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
						children: ALL_PANELS.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
							value: p,
							children: PANEL_LABELS[p]
						}, p))
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Decision"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
						value: formData.operator_decision,
						onChange: (e) => {
							const decision = e.target.value;
							setFormData({
								...formData,
								operator_decision: decision,
								corrected_class: decision === "reclassify" ? formData.corrected_class || "dent" : null
							});
						},
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "confirm",
								children: "Confirm"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "reject",
								children: "Reject (False Positive)"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "reclassify",
								children: "Reclassify"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "unclear",
								children: "Unclear"
							})
						]
					})]
				}),
				formData.operator_decision === "reclassify" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Corrected Class"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
						value: formData.corrected_class || "",
						onChange: (e) => setFormData({
							...formData,
							corrected_class: e.target.value
						}),
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
						children: DEFECT_CLASSES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
							value: c.id,
							children: c.label
						}, c.id))
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2 md:col-span-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Notes"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
						value: formData.notes || "",
						onChange: (e) => setFormData({
							...formData,
							notes: e.target.value
						}),
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px]",
						placeholder: "Optional notes..."
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "md:col-span-2 flex justify-end",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "submit",
						disabled: submitting,
						className: "px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50",
						children: submitting ? "Submitting..." : "Submit Review"
					})
				})
			]
		})]
	});
}
function ReviewEditForm({ editDecision, editCorrectedClass, setEditDecision, setEditCorrectedClass, onSave, onCancel, updating }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex flex-wrap items-center gap-3 rounded border border-border bg-background p-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
				className: "text-xs font-medium",
				children: "Decision:"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
				value: editDecision,
				onChange: (e) => setEditDecision(e.target.value),
				className: "rounded border border-input bg-background px-2 py-1 text-xs",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "confirm",
						children: "Confirm"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "reject",
						children: "Reject"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "reclassify",
						children: "Reclassify"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "unclear",
						children: "Unclear"
					})
				]
			}),
			editDecision === "reclassify" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
				className: "text-xs font-medium",
				children: "Corrected:"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
				value: editCorrectedClass,
				onChange: (e) => setEditCorrectedClass(e.target.value),
				className: "rounded border border-input bg-background px-2 py-1 text-xs",
				children: DEFECT_CLASSES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
					value: c.id,
					children: c.label
				}, c.id))
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
				onClick: onSave,
				disabled: updating,
				className: "rounded bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50",
				children: updating ? "Saving..." : "Save"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
				onClick: onCancel,
				className: "rounded border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-accent",
				children: "Cancel"
			})
		]
	});
}
function ReviewHistoryList({ reviews, loading, error, editingId, editDecision, editCorrectedClass, setEditDecision, setEditCorrectedClass, onEdit, onDelete, onSave, onCancel, updating }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-lg border border-border bg-card",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "p-4 border-b border-border",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
					className: "text-lg font-medium",
					children: [
						"Review History (",
						reviews.length,
						")"
					]
				})
			}),
			loading && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "p-8 text-center text-muted-foreground",
				children: "Loading reviews..."
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "p-8 text-center text-destructive",
				children: ["Error: ", error]
			}),
			!loading && !error && reviews.length === 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "p-8 text-center text-muted-foreground",
				children: "No reviews submitted yet. Use the form above to test the POST endpoint."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "divide-y divide-border",
				children: reviews.map((review) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "p-4 space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid grid-cols-1 md:grid-cols-5 gap-2 text-sm",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono text-xs text-muted-foreground",
									children: "ID:"
								}),
								" ",
								review.id
							] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono text-xs text-muted-foreground",
									children: "Insp:"
								}),
								" ",
								review.inspection_id
							] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono text-xs text-muted-foreground",
									children: "Pred:"
								}),
								" ",
								review.predicted_class,
								" / ",
								review.predicted_panel
							] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono text-xs text-muted-foreground",
									children: "Decision:"
								}),
								" ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
									tone: DECISION_TONE_MAP[review.operator_decision],
									size: "md",
									children: review.operator_decision
								}),
								review.corrected_class && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
									className: "ml-2 text-xs",
									children: ["→ ", review.corrected_class]
								})
							] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex items-center justify-end gap-2",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
										onClick: () => onEdit(review),
										className: "rounded border border-border px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground",
										children: "Edit"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
										onClick: () => onDelete(review.id),
										className: "rounded border border-red-500/40 px-2 py-0.5 text-xs text-red-500 hover:bg-red-500/10",
										children: "Delete"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "text-xs text-muted-foreground",
										children: new Date(review.created_at).toLocaleString()
									})
								]
							})
						]
					}), editingId === review.id && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewEditForm, {
						review,
						editDecision,
						editCorrectedClass,
						setEditDecision,
						setEditCorrectedClass,
						onSave: () => onSave(review.id),
						onCancel,
						updating
					})]
				}, review.id))
			})
		]
	});
}
function ReviewDashboard() {
	const [reviews, setReviews] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const [formData, setFormData] = (0, import_react.useState)(createEmptyReviewForm());
	const [submitting, setSubmitting] = (0, import_react.useState)(false);
	const [editingId, setEditingId] = (0, import_react.useState)(null);
	const [editDecision, setEditDecision] = (0, import_react.useState)("confirm");
	const [editCorrectedClass, setEditCorrectedClass] = (0, import_react.useState)("scratch");
	const [updating, setUpdating] = (0, import_react.useState)(false);
	const [deleteReviewId, setDeleteReviewId] = (0, import_react.useState)(null);
	const loadReviews = async () => {
		try {
			setLoading(true);
			setReviews(await fetchReviewQueue());
			setError(null);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to load reviews");
		} finally {
			setLoading(false);
		}
	};
	(0, import_react.useEffect)(() => {
		loadReviews();
	}, []);
	const handleEdit = (review) => {
		setEditingId(review.id);
		setEditDecision(review.operator_decision);
		setEditCorrectedClass(review.corrected_class || "scratch");
	};
	const handleDelete = (reviewId) => setDeleteReviewId(reviewId);
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
	const handleUpdate = async (reviewId) => {
		setUpdating(true);
		try {
			await updateReview(reviewId, {
				operator_decision: editDecision,
				corrected_class: editDecision === "reclassify" ? editCorrectedClass : null
			});
			setEditingId(null);
			toast.success("Review updated");
			await loadReviews();
		} catch (e) {
			toast.error("Failed to update review: " + (e instanceof Error ? e.message : String(e)));
		} finally {
			setUpdating(false);
		}
	};
	const handleSubmit = async (e) => {
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
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "p-6 space-y-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
				className: "text-2xl font-semibold tracking-tight",
				children: "Review Queue & History"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted-foreground mt-1",
				children: "Operator feedback loop. Currently showing the latest 50 submitted reviews from the backend."
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewSubmitForm, {
				formData,
				setFormData,
				onSubmit: handleSubmit,
				submitting
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewHistoryList, {
				reviews,
				loading,
				error,
				editingId,
				editDecision,
				editCorrectedClass,
				setEditDecision,
				setEditCorrectedClass,
				onEdit: handleEdit,
				onDelete: handleDelete,
				onSave: handleUpdate,
				onCancel: () => setEditingId(null),
				updating
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ConfirmDialog, {
				open: deleteReviewId !== null,
				onOpenChange: (o) => {
					if (!o) setDeleteReviewId(null);
				},
				title: "Delete review?",
				description: "The review will be permanently removed. This cannot be undone.",
				confirmLabel: "Delete Review",
				onConfirm: confirmDeleteReview
			})
		]
	});
}
function ReviewPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewDashboard, {});
}
//#endregion
export { ReviewPage as component };
