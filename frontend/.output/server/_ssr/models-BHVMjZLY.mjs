import { n as __toESM } from "../_runtime.mjs";
import { B as listCheckpoints, J as rollbackModel, K as registerCheckpoint, P as getSurgeryStatus, Q as scanCheckpoints, U as listTaxonomies, W as promoteModel, at as updateTaxonomy, d as deployModel, et as startSurgery, f as evaluateModelGates, i as createTaxonomy, o as deleteCheckpoint, u as deleteTaxonomy, w as fetchModelRegistryModels } from "./apiClient-ClfACpV5.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { t as Button } from "./button-BkEeRci-.mjs";
import { a as AlertDialogDescription, c as AlertDialogTitle, i as AlertDialogContent, l as StatusBadge, n as AlertDialogAction, o as AlertDialogFooter, r as AlertDialogCancel, s as AlertDialogHeader, t as AlertDialog } from "./alert-dialog-DsQ-Uqlb.mjs";
import { F as Circle, M as Crown, Y as ArrowDown, d as Scissors, f as Rocket, g as Pencil, m as Plus, n as X, o as Trash2, p as RefreshCw, q as ArrowUp, v as LoaderCircle } from "../_libs/lucide-react.mjs";
import { a as DialogHeader, i as DialogFooter, n as DialogContent, o as DialogTitle, r as DialogDescription, s as EmptyState, t as Dialog } from "./dialog-BTaDPjwY.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { n as PageShell, t as PageHeader } from "./PageShell-CQ88Jn3b.mjs";
import { n as Item2, r as Root2, t as Indicator } from "../_libs/@radix-ui/react-radio-group+[...].mjs";
import { a as SelectTrigger, i as SelectItem, n as Select, o as SelectValue, r as SelectContent, t as Label } from "./label-CsQhRIhI.mjs";
import { a as TabsList, i as TabsContent, n as Input, o as TabsTrigger, r as Tabs, s as TaxonomyPicker, t as CheckpointPicker } from "./tabs-DtPBE-s0.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/models-BHVMjZLY.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var STATUS_TONE_MAP = {
	candidate: "yellow",
	champion: "green",
	deployed: "blue",
	archived: "gray",
	rejected: "red"
};
var STAGE_LABEL_MAP = {
	stage1: "Stage 1 (SOD)",
	stage2: "Stage 2 (Defect)",
	stage3: "Stage 3 (Panel)"
};
function formatMetricValue(value) {
	if (value === null || value === void 0) return "—";
	if (typeof value === "number") return value.toFixed(4);
	return String(value);
}
function formatDate$2(isoString) {
	if (!isoString) return "—";
	return new Date(isoString).toLocaleString();
}
function getPrimaryMetric(metrics, stage) {
	if (stage === "stage1") {
		const recall = metrics["recall"];
		return {
			key: "Recall",
			value: formatMetricValue(recall)
		};
	}
	const map50 = metrics["test_mask_map50"];
	return {
		key: "mAP50",
		value: formatMetricValue(map50)
	};
}
function shortDatasetName(path) {
	if (!path) return "—";
	const segments = path.split("/").filter(Boolean);
	if (segments.length === 0) return "—";
	const last = segments[segments.length - 1];
	if (last.endsWith(".yaml") || last.endsWith(".yml")) return segments.length > 1 ? segments[segments.length - 2] : last;
	return last;
}
function ModelListTable({ models, selectedId, onSelect }) {
	if (models.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "No models registered yet",
		hint: "Launch a training job to create candidates."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "overflow-x-auto rounded-lg border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
			className: "w-full table-fixed text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
				className: "border-b bg-muted/50",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "w-[110px] px-3 py-3 text-left font-medium",
						children: "Stage"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "w-[20%] px-3 py-3 text-left font-medium",
						children: "Name"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "w-[15%] px-3 py-3 text-left font-medium",
						children: "Version"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-3 text-left font-medium",
						children: "Dataset"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "w-[110px] px-3 py-3 text-left font-medium",
						children: "Metric"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "w-[95px] px-3 py-3 text-left font-medium",
						children: "Status"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "w-[150px] px-3 py-3 text-left font-medium",
						children: "Created"
					})
				]
			}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: models.map((model) => {
				const metric = getPrimaryMetric(model.metrics, model.stage);
				return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					onClick: () => onSelect(model),
					className: `cursor-pointer border-b transition-colors hover:bg-muted/50 ${model.id === selectedId ? "bg-primary/5" : ""}`,
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "truncate px-3 py-3",
							title: STAGE_LABEL_MAP[model.stage],
							children: STAGE_LABEL_MAP[model.stage]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "truncate px-3 py-3 font-medium",
							title: model.model_name,
							children: model.model_name
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "truncate px-3 py-3 font-mono text-xs",
							title: model.version,
							children: model.version
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "truncate px-3 py-3 text-muted-foreground",
							title: model.dataset_version || void 0,
							children: shortDatasetName(model.dataset_version)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("td", {
							className: "truncate px-3 py-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: "text-muted-foreground",
								children: [metric.key, ": "]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "font-medium",
								children: metric.value
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
								tone: STATUS_TONE_MAP[model.status],
								size: "md",
								children: model.status
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "truncate px-3 py-3 text-muted-foreground",
							children: formatDate$2(model.created_at)
						})
					]
				}, model.id);
			}) })]
		})
	});
}
function ModelDetailPanel({ model, onPromote, onDeploy, onRollback }) {
	if (!model) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "flex h-full items-center justify-center text-muted-foreground",
		children: "Select a model to view details"
	});
	const metricEntries = Object.entries(model.metrics);
	const gateEntries = model.evaluation_report?.gates;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-6 p-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "break-all text-xl font-semibold",
						children: model.model_name
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
						tone: STATUS_TONE_MAP[model.status],
						size: "md",
						children: model.status
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "text-sm text-muted-foreground",
					children: [
						STAGE_LABEL_MAP[model.stage],
						" · v",
						model.version
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid grid-cols-2 gap-4 rounded-lg border p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "min-w-0",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Dataset"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm font-medium",
								children: shortDatasetName(model.dataset_version)
							}),
							model.dataset_version && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "break-all text-xs text-muted-foreground",
								children: model.dataset_version
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Training Run"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "break-all font-mono text-xs",
							children: model.training_run_id || "—"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Created"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm",
							children: formatDate$2(model.created_at)
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Promoted"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm",
							children: formatDate$2(model.promoted_at)
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Deployed"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm",
							children: formatDate$2(model.deployed_at)
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Config Hash"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "break-all font-mono text-xs",
							children: model.config_hash || "—"
						})]
					})
				]
			}),
			metricEntries.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
					className: "text-sm font-medium",
					children: "Metrics"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid grid-cols-2 gap-2 rounded-lg border p-4",
					children: metricEntries.map(([key, value]) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-xs text-muted-foreground",
						children: key
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm font-medium",
						children: formatMetricValue(value)
					})] }, key))
				})]
			}),
			gateEntries && gateEntries.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
					className: "text-sm font-medium",
					children: "Evaluation Gates"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "space-y-1 rounded-lg border p-4",
					children: gateEntries.map((gate) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center gap-2 text-sm",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: gate.passed ? "text-green-600" : "text-red-600",
								children: gate.passed ? "✓" : "✗"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "font-medium",
								children: gate.gate_name
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-muted-foreground",
								children: gate.reason
							})
						]
					}, gate.gate_name))
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex gap-2 border-t pt-4",
				children: [
					model.status === "candidate" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: () => onPromote(model),
						variant: "default",
						size: "sm",
						children: "Promote to Champion"
					}),
					model.status === "champion" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: () => onDeploy(model),
						variant: "default",
						size: "sm",
						children: "Deploy to Production"
					}),
					model.status === "deployed" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: () => onRollback(model),
						variant: "outline",
						size: "sm",
						children: "Rollback"
					})
				]
			})
		]
	});
}
function PromoteDialog({ candidate, champion, gateResults, isLoading, onConfirm, onClose }) {
	if (!candidate) return null;
	const allPassed = gateResults ? gateResults.every((g) => g.passed) : true;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open: true,
		onOpenChange: (o) => {
			if (!o) onClose();
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-lg",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Promote to Champion" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogDescription, { children: [
					STAGE_LABEL_MAP[candidate.stage],
					" · ",
					candidate.model_name,
					" v",
					candidate.version
				] })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-4 grid grid-cols-2 gap-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-lg border p-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Candidate"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-sm font-medium",
								children: candidate.model_name
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "mt-2 space-y-1",
								children: Object.entries(candidate.metrics).slice(0, 4).map(([key, value]) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
									className: "text-xs",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
										className: "text-muted-foreground",
										children: [key, ": "]
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "font-medium",
										children: formatMetricValue(value)
									})]
								}, key))
							})
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-lg border p-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Current Champion"
						}), champion ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm font-medium",
							children: champion.model_name
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "mt-2 space-y-1",
							children: Object.entries(champion.metrics).slice(0, 4).map(([key, value]) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "text-xs",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
									className: "text-muted-foreground",
									children: [key, ": "]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-medium",
									children: formatMetricValue(value)
								})]
							}, key))
						})] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-2 text-xs text-muted-foreground",
							children: "No champion exists yet"
						})]
					})]
				}),
				gateResults && gateResults.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-4 space-y-1 rounded-lg border p-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-xs font-medium text-muted-foreground",
						children: "Evaluation Gates"
					}), gateResults.map((gate) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center gap-2 text-sm",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: gate.passed ? "text-green-600" : "text-red-600",
								children: gate.passed ? "✓" : "✗"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: gate.gate_name }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "ml-auto text-xs text-muted-foreground",
								children: gate.reason
							})
						]
					}, gate.gate_name))]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					size: "sm",
					onClick: onClose,
					disabled: isLoading,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					size: "sm",
					onClick: onConfirm,
					disabled: isLoading || !allPassed,
					children: isLoading ? "Promoting..." : "Confirm Promotion"
				})] }),
				!allPassed && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs text-red-600",
					children: "Promotion blocked: one or more evaluation gates failed."
				})
			]
		})
	});
}
function DeployDialog({ model, isLoading, onConfirm, onClose }) {
	if (!model) return null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open: true,
		onOpenChange: (o) => {
			if (!o) onClose();
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-md",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Deploy to Production" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogDescription, { children: [
					"This will update the active model symlink for",
					" ",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "font-medium text-foreground",
						children: STAGE_LABEL_MAP[model.stage]
					}),
					"."
				] })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm text-yellow-800",
						children: "The inspection pipeline will immediately start using this model for new inspections. Ensure it has been validated against your test cases."
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-4 rounded-lg border p-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Model"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-sm font-medium",
							children: [
								model.model_name,
								" v",
								model.version
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Dataset"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm",
							children: model.dataset_version || "—"
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					size: "sm",
					onClick: onClose,
					disabled: isLoading,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					size: "sm",
					onClick: onConfirm,
					disabled: isLoading,
					children: isLoading ? "Deploying..." : "Confirm Deployment"
				})] })
			]
		})
	});
}
function RollbackDialog({ model, isLoading, onConfirm, onClose }) {
	if (!model) return null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "w-full max-w-md rounded-lg border bg-background p-6 shadow-lg",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "text-lg font-semibold",
					children: "Rollback Model"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: [
						"This will revert the production model for",
						" ",
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "font-medium text-foreground",
							children: STAGE_LABEL_MAP[model.stage]
						}),
						" ",
						"to the previously deployed version."
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-4 rounded-lg border border-red-200 bg-red-50 p-3",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "text-sm text-red-800",
						children: [
							"⚠️ The current deployed model (",
							model.model_name,
							" v",
							model.version,
							") will be archived and replaced by the previous version."
						]
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-6 flex justify-end gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "outline",
						size: "sm",
						onClick: onClose,
						disabled: isLoading,
						children: "Cancel"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						size: "sm",
						variant: "destructive",
						onClick: onConfirm,
						disabled: isLoading,
						children: isLoading ? "Rolling back..." : "Confirm Rollback"
					})]
				})
			]
		})
	});
}
function ModelRegistryDashboard() {
	const [models, setModels] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const [selectedModel, setSelectedModel] = (0, import_react.useState)(null);
	const [promoteTarget, setPromoteTarget] = (0, import_react.useState)(null);
	const [deployTarget, setDeployTarget] = (0, import_react.useState)(null);
	const [rollbackTarget, setRollbackTarget] = (0, import_react.useState)(null);
	const [gateResults, setGateResults] = (0, import_react.useState)(null);
	const [actionLoading, setActionLoading] = (0, import_react.useState)(false);
	const [actionMessage, setActionMessage] = (0, import_react.useState)(null);
	const loadModels = (0, import_react.useCallback)(async () => {
		try {
			setLoading(true);
			setError(null);
			setModels((await fetchModelRegistryModels()).models);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to load models");
		} finally {
			setLoading(false);
		}
	}, []);
	(0, import_react.useEffect)(() => {
		loadModels();
	}, [loadModels]);
	const currentChampion = promoteTarget ? models.find((m) => m.stage === promoteTarget.stage && m.status === "champion") ?? null : null;
	const handleOpenPromote = async (model) => {
		setPromoteTarget(model);
		setGateResults(null);
		try {
			setGateResults((await evaluateModelGates(model.id)).gate_results);
		} catch {
			setGateResults([]);
		}
	};
	const handleConfirmPromote = async () => {
		if (!promoteTarget) return;
		setActionLoading(true);
		try {
			setActionMessage((await promoteModel(promoteTarget.id)).message);
			setPromoteTarget(null);
			await loadModels();
		} catch (err) {
			setActionMessage(err instanceof Error ? err.message : "Promotion failed");
		} finally {
			setActionLoading(false);
		}
	};
	const handleConfirmDeploy = async () => {
		if (!deployTarget) return;
		setActionLoading(true);
		try {
			setActionMessage((await deployModel(deployTarget.id)).message);
			setDeployTarget(null);
			await loadModels();
		} catch (err) {
			setActionMessage(err instanceof Error ? err.message : "Deployment failed");
		} finally {
			setActionLoading(false);
		}
	};
	const handleConfirmRollback = async () => {
		if (!rollbackTarget) return;
		setActionLoading(true);
		try {
			setActionMessage((await rollbackModel(rollbackTarget.stage)).message);
			setRollbackTarget(null);
			await loadModels();
		} catch (err) {
			setActionMessage(err instanceof Error ? err.message : "Rollback failed");
		} finally {
			setActionLoading(false);
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "mx-auto max-w-7xl space-y-6 p-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
				className: "text-2xl font-semibold",
				children: "Model Registry"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted-foreground",
				children: "Manage model versions, promotion gates, and production deployment."
			})] }),
			actionMessage && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: actionMessage }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					onClick: () => setActionMessage(null),
					className: "font-medium hover:text-blue-950",
					children: "✕"
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-800",
				children: error
			}),
			loading ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "flex items-center justify-center py-12 text-muted-foreground",
				children: "Loading models..."
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid grid-cols-1 gap-6 lg:grid-cols-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "min-w-0 lg:col-span-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelListTable, {
						models,
						selectedId: selectedModel?.id ?? null,
						onSelect: setSelectedModel
					})
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "min-w-0 rounded-lg border",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelDetailPanel, {
						model: selectedModel,
						onPromote: handleOpenPromote,
						onDeploy: setDeployTarget,
						onRollback: setRollbackTarget
					})
				})]
			}),
			promoteTarget && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PromoteDialog, {
				candidate: promoteTarget,
				champion: currentChampion,
				gateResults,
				isLoading: actionLoading,
				onConfirm: handleConfirmPromote,
				onClose: () => setPromoteTarget(null)
			}),
			deployTarget && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DeployDialog, {
				model: deployTarget,
				isLoading: actionLoading,
				onConfirm: handleConfirmDeploy,
				onClose: () => setDeployTarget(null)
			}),
			rollbackTarget && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RollbackDialog, {
				model: rollbackTarget,
				isLoading: actionLoading,
				onConfirm: handleConfirmRollback,
				onClose: () => setRollbackTarget(null)
			})
		]
	});
}
function ModelTrackCard({ model }) {
	const metric = getPrimaryMetric(model.metrics, model.stage);
	const isChampion = model.status === "champion";
	const isDeployed = model.status === "deployed";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: cn("w-44 shrink-0 rounded-md border border-border bg-card p-3", isChampion && "border-status-pass/50 bg-status-pass/5", isDeployed && "border-primary/50 bg-primary/5"),
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between gap-1",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "truncate font-mono text-[10px] text-muted-foreground",
					children: ["v", model.version]
				}), isDeployed ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Rocket, { className: "h-3.5 w-3.5 shrink-0 text-primary" }) : isChampion ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Crown, { className: "h-3.5 w-3.5 shrink-0 text-status-pass" }) : null]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-1 truncate text-xs font-medium",
				title: model.model_name,
				children: model.model_name
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-2",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
					tone: STATUS_TONE_MAP[model.status],
					children: model.status
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mt-2 flex items-center justify-between font-mono text-[10px] text-muted-foreground",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: metric.key }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "text-foreground",
					children: metric.value
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-1 font-mono text-[9px] text-muted-foreground/70",
				children: formatDate$2(model.created_at)
			})
		]
	});
}
var STATUS_ORDER = {
	deployed: 0,
	champion: 1,
	candidate: 2,
	rejected: 3,
	archived: 4
};
function ModelTrackLane({ stage, stageLabel, models }) {
	const sorted = [...models].sort((a, b) => {
		const ao = STATUS_ORDER[a.status] ?? 9;
		const bo = STATUS_ORDER[b.status] ?? 9;
		if (ao !== bo) return ao - bo;
		return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-lg border border-border bg-background p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mb-3 flex items-center gap-2",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-primary",
					children: stage
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
					className: "text-sm font-semibold",
					children: stageLabel
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: "ml-auto font-mono text-[10px] text-muted-foreground",
					children: [
						models.length,
						" model",
						models.length === 1 ? "" : "s"
					]
				})
			]
		}), sorted.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
			title: `No models for ${stageLabel}`,
			hint: "Train a model to populate this track."
		}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "flex gap-3 overflow-x-auto pb-2",
			children: sorted.map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelTrackCard, { model: m }, m.id))
		})]
	});
}
var TRACK_STAGES = [
	"stage1",
	"stage2",
	"stage3"
];
function ModelTracksView() {
	const [models, setModels] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		let cancelled = false;
		fetchModelRegistryModels().then((res) => {
			if (!cancelled) setModels(res.models);
		}).catch((e) => {
			if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load models");
		}).finally(() => {
			if (!cancelled) setLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, []);
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center justify-center p-12 text-muted-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-2 h-4 w-4 animate-spin" }), " Loading model tracks..."]
	});
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "Failed to load models",
		hint: error
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "space-y-4",
		children: TRACK_STAGES.map((stage) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelTrackLane, {
			stage,
			stageLabel: STAGE_LABEL_MAP[stage],
			models: models.filter((m) => m.stage === stage)
		}, stage))
	});
}
function TaxonomyEditor({ open, taxonomy, onClose, onSaved }) {
	const isEdit = !!taxonomy;
	const [name, setName] = (0, import_react.useState)("");
	const [stage, setStage] = (0, import_react.useState)("stage2");
	const [classes, setClasses] = (0, import_react.useState)([""]);
	const [saving, setSaving] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		if (open) {
			if (taxonomy) {
				setName(taxonomy.name);
				setStage(taxonomy.stage);
				setClasses(taxonomy.class_names.length > 0 ? [...taxonomy.class_names] : [""]);
			} else {
				setName("");
				setStage("stage2");
				setClasses([""]);
			}
			setError(null);
			setSaving(false);
		}
	}, [open, taxonomy]);
	const updateClass = (index, value) => {
		setClasses((prev) => prev.map((c, i) => i === index ? value : c));
	};
	const removeClass = (index) => {
		setClasses((prev) => prev.filter((_, i) => i !== index));
	};
	const moveClass = (index, direction) => {
		setClasses((prev) => {
			const next = [...prev];
			const target = index + direction;
			if (target < 0 || target >= next.length) return prev;
			[next[index], next[target]] = [next[target], next[index]];
			return next;
		});
	};
	const addClass = () => {
		setClasses((prev) => [...prev, ""]);
	};
	const validClasses = classes.map((c) => c.trim()).filter(Boolean);
	const handleSave = async () => {
		if (!name.trim()) {
			setError("Name is required.");
			return;
		}
		if (validClasses.length === 0) {
			setError("At least one class name is required.");
			return;
		}
		setSaving(true);
		setError(null);
		try {
			if (isEdit && taxonomy) await updateTaxonomy(taxonomy.id, {
				name: name.trim(),
				class_names: validClasses
			});
			else await createTaxonomy({
				name: name.trim(),
				stage,
				class_names: validClasses
			});
			onSaved();
			onClose();
		} catch (err) {
			setError(err instanceof Error ? err.message : "Save failed");
		} finally {
			setSaving(false);
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open,
		onOpenChange: (v) => {
			if (!v) onClose();
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-lg max-h-[85vh] overflow-y-auto",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: isEdit ? "Edit Taxonomy" : "New Taxonomy" }) }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-4",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
								htmlFor: "tax-name",
								children: "Name"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								id: "tax-name",
								value: name,
								onChange: (e) => setName(e.target.value),
								placeholder: "e.g. big-defects"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Stage" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: stage,
									onValueChange: (v) => setStage(v),
									disabled: isEdit,
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "stage1",
											children: "stage1"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "stage2",
											children: "stage2"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "stage3",
											children: "stage3"
										})
									] })]
								}),
								isEdit && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xs text-muted-foreground",
									children: "Stage cannot be changed after creation."
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Classes" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "space-y-2",
									children: classes.map((cls, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "flex items-center gap-1.5",
										children: [
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
												value: cls,
												onChange: (e) => updateClass(i, e.target.value),
												placeholder: `class_${i + 1}`,
												className: "flex-1"
											}),
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
												variant: "ghost",
												size: "sm",
												onClick: () => moveClass(i, -1),
												disabled: i === 0,
												title: "Move up",
												children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowUp, { className: "h-3.5 w-3.5" })
											}),
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
												variant: "ghost",
												size: "sm",
												onClick: () => moveClass(i, 1),
												disabled: i === classes.length - 1,
												title: "Move down",
												children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowDown, { className: "h-3.5 w-3.5" })
											}),
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
												variant: "ghost",
												size: "sm",
												onClick: () => removeClass(i),
												disabled: classes.length <= 1,
												title: "Remove",
												children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-3.5 w-3.5" })
											})
										]
									}, i))
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
									variant: "outline",
									size: "sm",
									onClick: addClass,
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "mr-1 h-3.5 w-3.5" }), "Add class"]
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md border border-border bg-muted/30 p-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "text-xs font-medium text-muted-foreground mb-1.5",
								children: [
									"Preview: ",
									validClasses.length,
									" class",
									validClasses.length !== 1 ? "es" : ""
								]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex flex-wrap gap-1",
								children: [validClasses.map((c, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "inline-block rounded-sm bg-secondary px-1.5 py-0.5 text-[10px] font-mono text-secondary-foreground",
									children: c
								}, i)), validClasses.length === 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "text-[10px] text-muted-foreground",
									children: "No classes yet"
								})]
							})]
						}),
						error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-sm text-destructive",
							children: error
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "ghost",
					onClick: onClose,
					disabled: saving,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: handleSave,
					disabled: saving,
					children: saving ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }), "Saving..."] }) : isEdit ? "Save Changes" : "Create"
				})] })
			]
		})
	});
}
var STAGE_BADGE = {
	stage1: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
	stage2: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
	stage3: "bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30"
};
function formatDate$1(iso) {
	return new Date(iso).toLocaleString();
}
function TaxonomyList() {
	const [taxonomies, setTaxonomies] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const [editorOpen, setEditorOpen] = (0, import_react.useState)(false);
	const [editingTaxonomy, setEditingTaxonomy] = (0, import_react.useState)(null);
	const [deleteTarget, setDeleteTarget] = (0, import_react.useState)(null);
	const [deleting, setDeleting] = (0, import_react.useState)(false);
	const load = (0, import_react.useCallback)(async () => {
		try {
			setLoading(true);
			setError(null);
			setTaxonomies((await listTaxonomies()).taxonomies);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to load taxonomies");
		} finally {
			setLoading(false);
		}
	}, []);
	(0, import_react.useEffect)(() => {
		load();
	}, [load]);
	const handleDelete = async () => {
		if (!deleteTarget) return;
		setDeleting(true);
		try {
			await deleteTaxonomy(deleteTarget.id);
			setDeleteTarget(null);
			await load();
		} catch (err) {
			const msg = err instanceof Error ? err.message : "Delete failed";
			if (msg.includes("409") || msg.includes("conflict")) setError(msg);
			else setError(msg);
			setDeleteTarget(null);
		} finally {
			setDeleting(false);
		}
	};
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center justify-center p-8 text-muted-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-2 h-4 w-4 animate-spin" }), " Loading taxonomies..."]
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					size: "sm",
					onClick: () => {
						setEditingTaxonomy(null);
						setEditorOpen(true);
					},
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "mr-1.5 h-4 w-4" }), "New taxonomy"]
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted-foreground",
				children: error
			}),
			taxonomies.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground",
				children: "No taxonomies found. Create one to get started."
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "overflow-x-auto rounded-lg border border-border",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
					className: "w-full text-sm",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
						className: "bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Name"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Stage"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-right font-medium",
								children: "Classes"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Updated"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-right font-medium",
								children: "Actions"
							})
						] })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
						className: "divide-y divide-border bg-card",
						children: taxonomies.map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
							className: "transition-colors hover:bg-muted/30",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 font-medium",
									children: t.name
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: `inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${STAGE_BADGE[t.stage]}`,
										children: t.stage
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 text-right font-mono text-xs",
									children: t.class_names.length
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 text-xs text-muted-foreground",
									children: formatDate$1(t.updated_at)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "flex justify-end gap-1",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
											variant: "ghost",
											size: "sm",
											onClick: () => {
												setEditingTaxonomy(t);
												setEditorOpen(true);
											},
											title: "Edit",
											children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pencil, { className: "h-3.5 w-3.5" })
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
											variant: "ghost",
											size: "sm",
											onClick: () => setDeleteTarget(t),
											title: "Delete",
											children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "h-3.5 w-3.5" })
										})]
									})
								})
							]
						}, t.id))
					})]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TaxonomyEditor, {
				open: editorOpen,
				taxonomy: editingTaxonomy,
				onClose: () => setEditorOpen(false),
				onSaved: load
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialog, {
				open: !!deleteTarget,
				onOpenChange: (open) => {
					if (!open) setDeleteTarget(null);
				},
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogTitle, { children: "Delete taxonomy" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogDescription, { children: [
					"Are you sure you want to delete \"",
					deleteTarget?.name,
					"\"? This cannot be undone."
				] })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogCancel, {
					disabled: deleting,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogAction, {
					onClick: handleDelete,
					disabled: deleting,
					className: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
					children: deleting ? "Deleting..." : "Delete"
				})] })] })
			})
		]
	});
}
var ORIGIN_BADGE = {
	native_coco: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
	trained: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
	surgery: "bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30"
};
function formatDate(iso) {
	return new Date(iso).toLocaleString();
}
function CheckpointList() {
	const [checkpoints, setCheckpoints] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const [scanning, setScanning] = (0, import_react.useState)(false);
	const [registerOpen, setRegisterOpen] = (0, import_react.useState)(false);
	const [registerName, setRegisterName] = (0, import_react.useState)("");
	const [registerPath, setRegisterPath] = (0, import_react.useState)("");
	const [registerStage, setRegisterStage] = (0, import_react.useState)("stage2");
	const [registerNc, setRegisterNc] = (0, import_react.useState)("");
	const [registering, setRegistering] = (0, import_react.useState)(false);
	const [registerError, setRegisterError] = (0, import_react.useState)(null);
	const [deleteTarget, setDeleteTarget] = (0, import_react.useState)(null);
	const [deleting, setDeleting] = (0, import_react.useState)(false);
	const load = (0, import_react.useCallback)(async () => {
		try {
			setLoading(true);
			setError(null);
			setCheckpoints((await listCheckpoints()).checkpoints);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to load checkpoints");
		} finally {
			setLoading(false);
		}
	}, []);
	(0, import_react.useEffect)(() => {
		load();
	}, [load]);
	const handleScan = async () => {
		setScanning(true);
		try {
			const res = await scanCheckpoints();
			toast.success(`Scan complete: registered ${res.registered}, skipped ${res.skipped}`);
			await load();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : "Scan failed");
		} finally {
			setScanning(false);
		}
	};
	const openRegister = () => {
		setRegisterName("");
		setRegisterPath("");
		setRegisterStage("stage2");
		setRegisterNc("");
		setRegisterError(null);
		setRegisterOpen(true);
	};
	const handleRegister = async () => {
		if (!registerName.trim() || !registerPath.trim()) {
			setRegisterError("Name and path are required.");
			return;
		}
		const nc = registerNc.trim() === "" ? void 0 : Number(registerNc);
		if (nc !== void 0 && (!Number.isFinite(nc) || nc < 0)) {
			setRegisterError("nc must be a non-negative number.");
			return;
		}
		setRegistering(true);
		setRegisterError(null);
		try {
			await registerCheckpoint({
				name: registerName.trim(),
				path: registerPath.trim(),
				stage: registerStage,
				nc
			});
			toast.success(`Registered checkpoint "${registerName.trim()}"`);
			setRegisterOpen(false);
			await load();
		} catch (err) {
			setRegisterError(err instanceof Error ? err.message : "Register failed");
		} finally {
			setRegistering(false);
		}
	};
	const handleDelete = async () => {
		if (!deleteTarget) return;
		setDeleting(true);
		try {
			await deleteCheckpoint(deleteTarget.id);
			toast.success(`Deleted checkpoint "${deleteTarget.name}"`);
			setDeleteTarget(null);
			await load();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : "Delete failed");
			setDeleteTarget(null);
		} finally {
			setDeleting(false);
		}
	};
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center justify-center p-8 text-muted-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-2 h-4 w-4 animate-spin" }), " Loading checkpoints..."]
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						variant: "outline",
						size: "sm",
						onClick: handleScan,
						disabled: scanning,
						children: [scanning ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RefreshCw, { className: "mr-1.5 h-4 w-4" }), "Scan"]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						size: "sm",
						onClick: openRegister,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "mr-1.5 h-4 w-4" }), "Register"]
					})]
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted-foreground",
				children: error
			}),
			checkpoints.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground",
				children: "No checkpoints registered. Scan the checkpoints directory or register one manually."
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "overflow-x-auto rounded-lg border border-border",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
					className: "w-full text-sm",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
						className: "bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Name"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Stage"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Origin"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-right font-medium",
								children: "NC"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-right font-medium",
								children: "Size"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Exists"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-left font-medium",
								children: "Created"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-4 py-3 text-right font-medium",
								children: "Actions"
							})
						] })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
						className: "divide-y divide-border bg-card",
						children: checkpoints.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
							className: "transition-colors hover:bg-muted/30",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 font-medium",
									children: c.name
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 text-xs text-muted-foreground",
									children: c.stage || "—"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: `inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${ORIGIN_BADGE[c.origin] ?? ORIGIN_BADGE.trained}`,
										children: c.origin
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 text-right font-mono text-xs",
									children: c.nc
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 text-right font-mono text-xs",
									children: c.size_mb != null ? `${c.size_mb.toFixed(1)} MB` : "—"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3",
									children: c.exists ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "inline-flex items-center rounded-full border border-green-500/30 bg-green-500/15 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-400",
										children: "ok"
									}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
										className: "inline-flex items-center rounded-full border border-red-500/30 bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400",
										children: "missing"
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3 text-xs text-muted-foreground",
									children: formatDate(c.created_at)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "px-4 py-3",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "flex justify-end",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
											variant: "ghost",
											size: "sm",
											onClick: () => setDeleteTarget(c),
											title: "Delete",
											children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "h-3.5 w-3.5" })
										})
									})
								})
							]
						}, c.id))
					})]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
				open: registerOpen,
				onOpenChange: (open) => !open && setRegisterOpen(false),
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
					className: "max-w-md",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Register Checkpoint" }) }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-3",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "cp-name",
										children: "Name"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										id: "cp-name",
										value: registerName,
										onChange: (e) => setRegisterName(e.target.value),
										placeholder: "e.g. yolo11n-sod"
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "cp-path",
										children: "Path"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										id: "cp-path",
										value: registerPath,
										onChange: (e) => setRegisterPath(e.target.value),
										placeholder: "models/stage1/yolo11n.pt"
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Stage" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
										value: registerStage,
										onValueChange: setRegisterStage,
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
												value: "stage1",
												children: "stage1"
											}),
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
												value: "stage2",
												children: "stage2"
											}),
											/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
												value: "stage3",
												children: "stage3"
											})
										] })]
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "cp-nc",
										children: "Number of classes (optional)"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										id: "cp-nc",
										type: "number",
										min: 0,
										value: registerNc,
										onChange: (e) => setRegisterNc(e.target.value),
										placeholder: "e.g. 7"
									})]
								}),
								registerError && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-sm text-destructive",
									children: registerError
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							onClick: () => setRegisterOpen(false),
							disabled: registering,
							children: "Cancel"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							onClick: handleRegister,
							disabled: registering,
							children: registering ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }), "Registering..."] }) : "Register"
						})] })
					]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialog, {
				open: !!deleteTarget,
				onOpenChange: (open) => {
					if (!open) setDeleteTarget(null);
				},
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogTitle, { children: "Delete checkpoint" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogDescription, { children: [
					"Are you sure you want to delete \"",
					deleteTarget?.name,
					"\"? This removes the registry entry only — the file on disk is untouched."
				] })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogCancel, {
					disabled: deleting,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogAction, {
					onClick: handleDelete,
					disabled: deleting,
					className: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
					children: deleting ? "Deleting..." : "Delete"
				})] })] })
			})
		]
	});
}
var RadioGroup = import_react.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Root2, {
		className: cn("grid gap-2", className),
		...props,
		ref
	});
});
RadioGroup.displayName = Root2.displayName;
var RadioGroupItem = import_react.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Item2, {
		ref,
		className: cn("aspect-square h-4 w-4 rounded-full border border-primary text-primary shadow cursor-pointer focus:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50", className),
		...props,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Indicator, {
			className: "flex items-center justify-center",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Circle, { className: "h-3.5 w-3.5 fill-primary" })
		})
	});
});
RadioGroupItem.displayName = Item2.displayName;
function HeadSurgeryDialog({ open, onOpenChange, onCompleted }) {
	const [sourceId, setSourceId] = (0, import_react.useState)(null);
	const [taxonomyId, setTaxonomyId] = (0, import_react.useState)(null);
	const [initMode, setInitMode] = (0, import_react.useState)("fresh");
	const [phase, setPhase] = (0, import_react.useState)("idle");
	const [jobId, setJobId] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	const [outputId, setOutputId] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		if (open) {
			setSourceId(null);
			setTaxonomyId(null);
			setInitMode("fresh");
			setPhase("idle");
			setJobId(null);
			setError(null);
			setOutputId(null);
		}
	}, [open]);
	(0, import_react.useEffect)(() => {
		if (!jobId || phase !== "running") return;
		let cancelled = false;
		const timer = setInterval(async () => {
			try {
				const st = await getSurgeryStatus(jobId);
				if (cancelled) return;
				if (st.status === "completed") {
					setPhase("done");
					setOutputId(st.output_checkpoint_id);
					toast.success("Head surgery completed");
					onCompleted?.();
				} else if (st.status === "failed") {
					setPhase("failed");
					setError(st.error_message ?? "Surgery failed");
					toast.error("Head surgery failed");
				}
			} catch {}
		}, 2e3);
		return () => {
			cancelled = true;
			clearInterval(timer);
		};
	}, [
		jobId,
		phase,
		onCompleted
	]);
	const canSubmit = sourceId != null && taxonomyId != null && phase !== "running";
	async function handleSubmit() {
		if (!sourceId || !taxonomyId) return;
		setPhase("running");
		setError(null);
		try {
			setJobId((await startSurgery({
				source_checkpoint_id: sourceId,
				taxonomy_id: taxonomyId,
				head_init_mode: initMode
			})).job_id);
		} catch (e) {
			setPhase("failed");
			setError(e instanceof Error ? e.message : "Failed to start surgery");
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open,
		onOpenChange,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-lg",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Head Surgery" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription, { children: "Remap a checkpoint head to a target taxonomy. Backbone weights are transferred; mismatched head tensors are re-initialized." })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-4",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Source checkpoint" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CheckpointPicker, {
								value: sourceId,
								onChange: setSourceId
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Target taxonomy" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TaxonomyPicker, {
								value: taxonomyId,
								onChange: setTaxonomyId
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Head init mode" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(RadioGroup, {
								value: initMode,
								onValueChange: (v) => setInitMode(v),
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-start gap-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RadioGroupItem, {
										value: "fresh",
										id: "init-fresh"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "init-fresh",
										className: "font-normal",
										children: "Fresh head init (recommended) — keep new random head weights"
									})]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-start gap-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RadioGroupItem, {
										value: "class_aware",
										id: "init-aware"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
										htmlFor: "init-aware",
										className: "font-normal",
										children: "Class-aware copy — copy overlapping class rows from source head"
									})]
								})]
							})]
						}),
						phase === "running" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "flex items-center gap-2 text-xs text-muted-foreground",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3.5 w-3.5 animate-spin" }), "Running surgery…"]
						}),
						phase === "done" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-xs text-status-pass",
							children: [
								"Done. New checkpoint registered",
								outputId ? ` (${outputId.slice(0, 8)}…)` : "",
								"."
							]
						}),
						phase === "failed" && error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-status-fail",
							children: error
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					size: "sm",
					onClick: () => onOpenChange(false),
					children: "Close"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					size: "sm",
					disabled: !canSubmit,
					onClick: handleSubmit,
					children: [phase === "running" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 animate-spin" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Scissors, { className: "h-4 w-4" }), "Run surgery"]
				})] })
			]
		})
	});
}
function ModelsPage() {
	const [showSurgery, setShowSurgery] = (0, import_react.useState)(false);
	const [refreshKey, setRefreshKey] = (0, import_react.useState)(0);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
		defaultValue: "registry",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageShell, {
				className: "space-y-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "registry",
						children: "Registry"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "tracks",
						children: "Tracks"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "taxonomies",
						children: "Taxonomies"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
						value: "checkpoints",
						children: "Checkpoints"
					})
				] })
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
				value: "registry",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelRegistryDashboard, {})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
				value: "tracks",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(PageShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
					title: "Model Tracks",
					subtitle: "Lifecycle view of candidates, champions, and deployed models per pipeline stage."
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelTracksView, {})] })
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
				value: "taxonomies",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(PageShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
					title: "Taxonomies",
					subtitle: "Define class taxonomies per pipeline stage."
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TaxonomyList, {})] })
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
				value: "checkpoints",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(PageShell, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
						title: "Checkpoints",
						subtitle: "Registered model weights available to pipeline stages.",
						actions: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							size: "sm",
							onClick: () => setShowSurgery(true),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Scissors, { className: "h-4 w-4" }), "Head Surgery"]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CheckpointList, {}, refreshKey),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(HeadSurgeryDialog, {
						open: showSurgery,
						onOpenChange: setShowSurgery,
						onCompleted: () => setRefreshKey((k) => k + 1)
					})
				] })
			})
		]
	});
}
//#endregion
export { ModelsPage as component };
