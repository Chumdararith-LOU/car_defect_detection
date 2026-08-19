import { n as __toESM } from "../_runtime.mjs";
import { S as fetchExperiments, x as fetchExperimentRuns } from "./apiClient-ClfACpV5.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { t as Button } from "./button-BkEeRci-.mjs";
import { P as Clock, T as FlaskConical, i as Trophy, p as RefreshCw } from "../_libs/lucide-react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/experiments-rMCI0Uv3.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function formatTimestamp(ts) {
	if (!ts) return "—";
	return new Date(parseInt(ts, 10)).toLocaleDateString();
}
function ExperimentList({ experiments, selectedId, onSelect, loading }) {
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "p-4 text-sm text-muted-foreground",
		children: "Loading experiments..."
	});
	if (experiments.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "p-4 text-sm text-muted-foreground",
		children: "No experiments found in MLflow."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "space-y-1",
		children: experiments.map((exp) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
			onClick: () => onSelect(exp.experiment_id),
			className: `w-full text-left rounded-md px-3 py-2.5 transition-colors ${selectedId === exp.experiment_id ? "bg-primary/10 text-primary border border-primary/30" : "hover:bg-muted border border-transparent"}`,
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center gap-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "h-3.5 w-3.5 shrink-0" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "text-sm font-medium truncate",
					children: exp.name
				})]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mt-1 flex items-center justify-between text-[10px] text-muted-foreground pl-5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [exp.run_count, " runs"] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: formatTimestamp(exp.latest_run_time) })]
			})]
		}, exp.experiment_id))
	});
}
var METRIC_KEYS = [
	"metrics/mAP50(M)",
	"metrics/mAP50-95(M)",
	"metrics/precision(M)",
	"metrics/recall(M)"
];
var METRIC_LABELS = {
	"metrics/mAP50(M)": "mAP50 (Mask)",
	"metrics/mAP50-95(M)": "mAP50-95 (Mask)",
	"metrics/precision(M)": "Precision",
	"metrics/recall(M)": "Recall"
};
var PARAM_KEYS = [
	"model_preset",
	"epochs",
	"imgsz",
	"batch_size",
	"loss_type"
];
function formatDuration(seconds) {
	if (seconds === null) return "—";
	if (seconds < 60) return `${Math.round(seconds)}s`;
	return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}
function getMetricValue(run, key) {
	const metric = run.metrics.find((m) => m.key === key);
	return metric ? metric.value : null;
}
function getParamValue(run, key) {
	const param = run.params.find((p) => p.key === key);
	return param ? param.value : null;
}
function findBestMetricValue(runs, key) {
	const values = runs.map((r) => getMetricValue(r, key)).filter((v) => v !== null);
	if (values.length === 0) return null;
	return Math.max(...values);
}
function RunComparisonTable({ runs, bestRunId }) {
	if (runs.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground",
		children: "Select an experiment to view its runs."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-x-auto rounded-lg border border-border",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
			className: "w-full text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
				className: "bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Run"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Status"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Duration"
					}),
					METRIC_KEYS.map((key) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-right font-medium",
						children: METRIC_LABELS[key]
					}, key))
				] })
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
				className: "divide-y divide-border bg-card",
				children: runs.map((run) => {
					const isBest = run.run_id === bestRunId;
					return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
						className: `transition-colors ${isBest ? "bg-green-500/5" : "hover:bg-muted/30"}`,
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-4 py-3",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-center gap-2",
									children: [isBest && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trophy, { className: "h-3.5 w-3.5 text-yellow-500" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
										className: "font-medium text-sm",
										children: run.run_name
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
										className: "text-[10px] font-mono text-muted-foreground",
										children: [run.run_id.substring(0, 8), "..."]
									})] })]
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-4 py-3",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${run.status === "FINISHED" ? "bg-green-500/15 text-green-700 dark:text-green-400" : run.status === "RUNNING" ? "bg-blue-500/15 text-blue-700 dark:text-blue-400" : "bg-gray-500/15 text-gray-700 dark:text-gray-400"}`,
									children: run.status
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-4 py-3 text-xs text-muted-foreground",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-center gap-1",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Clock, { className: "h-3 w-3" }), formatDuration(run.duration_seconds)]
								})
							}),
							METRIC_KEYS.map((key) => {
								const value = getMetricValue(run, key);
								const bestValue = findBestMetricValue(runs, key);
								return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: `px-4 py-3 text-right font-mono text-xs ${value !== null && value === bestValue ? "font-semibold text-green-600 dark:text-green-400" : "text-muted-foreground"}`,
									children: value !== null ? (value * 100).toFixed(1) + "%" : "—"
								}, key);
							})
						]
					}, run.run_id);
				})
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "border-t border-border bg-muted/30 p-4",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "overflow-x-auto",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
					className: "w-full text-xs",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
						className: "text-muted-foreground",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2 text-left font-medium",
							children: "Parameter"
						}), runs.map((run) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2 text-left font-medium",
							children: run.run_name
						}, run.run_id))]
					}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
						className: "font-mono",
						children: PARAM_KEYS.map((key) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
							className: "border-t border-border/50",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-4 py-2 text-muted-foreground",
								children: key
							}), runs.map((run) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-4 py-2",
								children: getParamValue(run, key) || "—"
							}, run.run_id))]
						}, key))
					})]
				})
			})
		})]
	});
}
function ExperimentDashboard() {
	const [experiments, setExperiments] = (0, import_react.useState)([]);
	const [selectedExpId, setSelectedExpId] = (0, import_react.useState)(null);
	const [runs, setRuns] = (0, import_react.useState)([]);
	const [bestRunId, setBestRunId] = (0, import_react.useState)(null);
	const [loadingExperiments, setLoadingExperiments] = (0, import_react.useState)(true);
	const [loadingRuns, setLoadingRuns] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	const loadExperiments = async () => {
		try {
			setLoadingExperiments(true);
			setError(null);
			const res = await fetchExperiments();
			setExperiments(res.experiments);
			if (res.experiments.length > 0 && !selectedExpId) setSelectedExpId(res.experiments[0].experiment_id);
		} catch (err) {
			setError(err.message || "Failed to load experiments");
		} finally {
			setLoadingExperiments(false);
		}
	};
	const loadRuns = async (expId) => {
		try {
			setLoadingRuns(true);
			const res = await fetchExperimentRuns(expId);
			setRuns(res.runs);
			let bestId = null;
			let bestMap = -1;
			for (const run of res.runs) {
				const map50 = run.metrics.find((m) => m.key === "metrics/mAP50(M)");
				if (map50 && map50.value > bestMap) {
					bestMap = map50.value;
					bestId = run.run_id;
				}
			}
			setBestRunId(bestId);
		} catch (err) {
			setError(err.message || "Failed to load runs");
		} finally {
			setLoadingRuns(false);
		}
	};
	(0, import_react.useEffect)(() => {
		loadExperiments();
	}, []);
	(0, import_react.useEffect)(() => {
		if (selectedExpId) loadRuns(selectedExpId);
	}, [selectedExpId]);
	const selectedExp = experiments.find((e) => e.experiment_id === selectedExpId);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "p-6 space-y-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-start justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h1", {
					className: "text-2xl font-semibold tracking-tight flex items-center gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "h-6 w-6" }), "Experiments"]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted-foreground mt-1",
					children: "Compare MLflow training runs and identify the best models."
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					variant: "outline",
					size: "sm",
					onClick: loadExperiments,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RefreshCw, { className: "h-4 w-4 mr-1.5" }), "Refresh"]
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive",
				children: error
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid grid-cols-12 gap-6",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "col-span-3",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-lg border border-border bg-card",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "border-b border-border px-4 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "text-sm font-semibold",
								children: "Experiments"
							})
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "p-2",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ExperimentList, {
								experiments,
								selectedId: selectedExpId,
								onSelect: setSelectedExpId,
								loading: loadingExperiments
							})
						})]
					})
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "col-span-9 space-y-4",
					children: [selectedExp && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "text-lg font-semibold",
							children: selectedExp.name
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "text-xs text-muted-foreground",
							children: [runs.length, " runs"]
						})]
					}), loadingRuns ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "rounded-lg border border-border bg-card p-8 text-center text-muted-foreground",
						children: "Loading runs..."
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RunComparisonTable, {
						runs,
						bestRunId
					})]
				})]
			})
		]
	});
}
function ExperimentsPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ExperimentDashboard, {});
}
//#endregion
export { ExperimentsPage as component };
